#include "test_util.h"

#include "protocol/frame.h"

#include <string.h>

/* 一次喂完整个缓冲，返回最后一次得到的事件 */
static frame_event_t feed(frame_parser_t *parser, const uint8_t *data, size_t len,
                          frame_t *out)
{
    frame_event_t event = FRAME_EVENT_NONE;
    size_t i;

    for (i = 0u; i < len; i++) {
        event = frame_parser_push(parser, data[i], out);
    }
    return event;
}

static void frame_roundtrip(void)
{
    frame_parser_t parser;
    frame_t out;
    uint8_t wire[FRAME_MAX_SIZE];
    const uint8_t payload[] = {0x10, 0x20, 0x30};
    size_t written;

    written = frame_encode(FRAME_TYPE_STATUS, payload, sizeof(payload), wire, sizeof(wire));
    CHECK_EQ(written, sizeof(payload) + FRAME_OVERHEAD);

    frame_parser_init(&parser);
    memset(&out, 0, sizeof(out));
    CHECK_EQ(feed(&parser, wire, written, &out), FRAME_EVENT_READY);
    CHECK_EQ(out.type, FRAME_TYPE_STATUS);
    CHECK_EQ(out.len, sizeof(payload));
    CHECK(memcmp(out.payload, payload, sizeof(payload)) == 0);
}

static void frame_zero_length_payload(void)
{
    frame_parser_t parser;
    frame_t out;
    uint8_t wire[FRAME_MAX_SIZE];
    size_t written;

    written = frame_encode(FRAME_TYPE_HEARTBEAT, NULL, 0u, wire, sizeof(wire));
    CHECK_EQ(written, FRAME_OVERHEAD);

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, wire, written, &out), FRAME_EVENT_READY);
    CHECK_EQ(out.type, FRAME_TYPE_HEARTBEAT);
    CHECK_EQ(out.len, 0u);
}

static void frame_max_payload(void)
{
    frame_parser_t parser;
    frame_t out;
    uint8_t wire[FRAME_MAX_SIZE];
    uint8_t payload[FRAME_MAX_PAYLOAD];
    size_t i;
    size_t written;

    for (i = 0u; i < FRAME_MAX_PAYLOAD; i++) {
        payload[i] = (uint8_t)(i * 7u + 1u);
    }
    written = frame_encode(FRAME_TYPE_CMD, payload, FRAME_MAX_PAYLOAD, wire, sizeof(wire));
    CHECK_EQ(written, FRAME_MAX_SIZE);

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, wire, written, &out), FRAME_EVENT_READY);
    CHECK_EQ(out.len, FRAME_MAX_PAYLOAD);
    CHECK(memcmp(out.payload, payload, FRAME_MAX_PAYLOAD) == 0);
}

static void frame_skips_leading_garbage(void)
{
    /* 上电时串口常收到半截数据或噪声，解析器要能自己走出来，不靠上层清缓冲。 */
    frame_parser_t parser;
    frame_t out;
    uint8_t garbage[] = {0x00, 0xAA, 0x13, 0xFF, 0xAA}; /* 末尾是一个假起点 */
    uint8_t good[FRAME_MAX_SIZE];
    size_t good_len = frame_encode(FRAME_TYPE_STATUS, (const uint8_t *)"ok", 2u,
                                   good, sizeof(good));

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, garbage, sizeof(garbage), &out), FRAME_EVENT_NONE);
    CHECK(parser.dropped_bytes >= 4u);
    /* 垃圾里最后一个 0xAA 正好与真帧的 0xAA 连成 0xAA 0xAA 0x55，仍应同步上 */
    CHECK_EQ(feed(&parser, good, good_len, &out), FRAME_EVENT_READY);
    CHECK_EQ(out.len, 2u);
}

static void frame_double_sof_byte_is_not_prefix(void)
{
    /* 0xAA 0xAA 0x55 必须被识别为一帧的起点，而不是丢弃 3 个字节。 */
    frame_parser_t parser;
    frame_t out;
    uint8_t frame_only[FRAME_MAX_SIZE];
    size_t frame_len = frame_encode(FRAME_TYPE_STATUS, (const uint8_t *)"x", 1u,
                                    frame_only, sizeof(frame_only));
    uint8_t prefix = FRAME_SOF0;

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, &prefix, 1u, &out), FRAME_EVENT_NONE);
    CHECK_EQ(feed(&parser, frame_only, frame_len, &out), FRAME_EVENT_READY);
    CHECK_EQ(out.len, 1u);
    CHECK_EQ(parser.dropped_bytes, 1u); /* 只丢了一个多余的 0xAA */
}

static void frame_bad_crc_detected_and_recovers(void)
{
    frame_parser_t parser;
    frame_t out;
    uint8_t bad[FRAME_MAX_SIZE];
    uint8_t good[FRAME_MAX_SIZE];
    size_t bad_len = frame_encode(FRAME_TYPE_CMD, (const uint8_t *)"ab", 2u,
                                  bad, sizeof(bad));
    size_t good_len = frame_encode(FRAME_TYPE_CMD, (const uint8_t *)"cd", 2u,
                                   good, sizeof(good));

    CHECK(bad_len > 0u && good_len > 0u);
    bad[bad_len - 1u] ^= 0x01u; /* 只翻 CRC 最后一位 */

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, bad, bad_len, &out), FRAME_EVENT_BAD_CRC);
    CHECK_EQ(parser.bad_crc_count, 1u);
    /* 坏帧之后必须还能正确收下一帧：不做这一步，丢帧会连累后续 */
    CHECK_EQ(feed(&parser, good, good_len, &out), FRAME_EVENT_READY);
    CHECK(memcmp(out.payload, "cd", 2u) == 0);
}

static void frame_payload_corruption_detected(void)
{
    frame_parser_t parser;
    frame_t out;
    uint8_t wire[FRAME_MAX_SIZE];
    size_t written = frame_encode(FRAME_TYPE_STATUS, (const uint8_t *)"abc", 3u,
                                  wire, sizeof(wire));

    CHECK(written > 0u);
    wire[5] ^= 0x08u; /* 改 payload 的 1 个 bit，CRC 应发现 */

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, wire, written, &out), FRAME_EVENT_BAD_CRC);
}

static void frame_oversize_rejected(void)
{
    frame_parser_t parser;
    frame_t out;
    uint8_t wire[6];

    wire[0] = FRAME_SOF0;
    wire[1] = FRAME_SOF1;
    wire[2] = FRAME_TYPE_STATUS;
    wire[3] = (uint8_t)(FRAME_MAX_PAYLOAD + 1u);

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, wire, 4u, &out), FRAME_EVENT_OVERSIZE);
    CHECK_EQ(parser.oversize_count, 1u);
}

static void frame_truncated_without_reset_swallows_next(void)
{
    /* 这条测试记录一个**已知限制**，不是在夸解析器：
     * 半截帧（发一半掉电、线被拔）后不调用 frame_parser_reset()，
     * 下一帧的 0xAA 0x55 会被当作 TYPE/LEN 吃掉，表现为"偶发丢一整帧"。
     * 解药是上层在字节间超时后复位 —— 见下一条测试。 */
    frame_parser_t parser;
    frame_t out;
    uint8_t good[FRAME_MAX_SIZE];
    size_t good_len = frame_encode(FRAME_TYPE_STATUS, (const uint8_t *)"zz", 2u,
                                   good, sizeof(good));

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, good, 2u, &out), FRAME_EVENT_NONE); /* 只有 SOF，卡在帧中 */
    CHECK(feed(&parser, good, good_len, &out) != FRAME_EVENT_READY);
}

static void frame_truncated_then_reset_recovers(void)
{
    /* 正确用法：字节间隔超时 → 复位 → 下一帧正常解出。 */
    frame_parser_t parser;
    frame_t out;
    uint8_t good[FRAME_MAX_SIZE];
    size_t good_len = frame_encode(FRAME_TYPE_STATUS, (const uint8_t *)"zz", 2u,
                                   good, sizeof(good));

    frame_parser_init(&parser);
    CHECK_EQ(feed(&parser, good, 2u, &out), FRAME_EVENT_NONE);
    frame_parser_reset(&parser);
    CHECK_EQ(feed(&parser, good, good_len, &out), FRAME_EVENT_READY);
    CHECK_EQ(out.len, 2u);
    /* 复位不清统计：丢帧率仍能反映刚才那半截帧 */
    frame_parser_reset(&parser);
    CHECK(parser.state == 0u);
}

static void frame_encode_rejects_bad_args(void)
{
    uint8_t wire[FRAME_MAX_SIZE];
    uint8_t payload[FRAME_MAX_PAYLOAD + 1u];

    memset(payload, 0, sizeof(payload));
    CHECK_EQ(frame_encode(FRAME_TYPE_CMD, payload, FRAME_MAX_PAYLOAD + 1u,
                          wire, sizeof(wire)), 0);
    CHECK_EQ(frame_encode(FRAME_TYPE_CMD, payload, 4u, wire, 8u), 0);   /* 容量不足 */
    CHECK_EQ(frame_encode(FRAME_TYPE_CMD, NULL, 4u, wire, sizeof(wire)), 0);
    CHECK_EQ(frame_encode(FRAME_TYPE_CMD, payload, 4u, NULL, sizeof(wire)), 0);
}

static void frame_parser_null_safe(void)
{
    frame_t out;

    frame_parser_init(NULL);
    CHECK_EQ(frame_parser_push(NULL, 0x00, &out), FRAME_EVENT_NONE);
}

void suite_frame(void)
{
    frame_roundtrip();
    frame_zero_length_payload();
    frame_max_payload();
    frame_skips_leading_garbage();
    frame_double_sof_byte_is_not_prefix();
    frame_bad_crc_detected_and_recovers();
    frame_payload_corruption_detected();
    frame_oversize_rejected();
    frame_truncated_without_reset_swallows_next();
    frame_truncated_then_reset_recovers();
    frame_encode_rejects_bad_args();
    frame_parser_null_safe();
}
