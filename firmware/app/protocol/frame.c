#include "protocol/frame.h"

#include <string.h>

enum {
    FRAME_STATE_SOF0 = 0,
    FRAME_STATE_SOF1,
    FRAME_STATE_TYPE,
    FRAME_STATE_LEN,
    FRAME_STATE_PAYLOAD,
    FRAME_STATE_CRC
};

static void parser_reset(frame_parser_t *parser)
{
    parser->state = (uint8_t)FRAME_STATE_SOF0;
    parser->type = 0u;
    parser->len = 0u;
    parser->index = 0u;
    parser->crc = 0u;
}

void frame_parser_init(frame_parser_t *parser)
{
    if (parser == NULL) {
        return;
    }
    memset(parser, 0, sizeof(*parser));
    parser_reset(parser);
}

void frame_parser_reset(frame_parser_t *parser)
{
    if (parser == NULL) {
        return;
    }
    parser_reset(parser);
}

frame_event_t frame_parser_push(frame_parser_t *parser, uint8_t byte, frame_t *out)
{
    if (parser == NULL || out == NULL) {
        return FRAME_EVENT_NONE;
    }

    switch (parser->state) {
    case FRAME_STATE_SOF0:
        if (byte == FRAME_SOF0) {
            parser->state = (uint8_t)FRAME_STATE_SOF1;
        } else {
            parser->dropped_bytes++;
        }
        break;

    case FRAME_STATE_SOF1:
        if (byte == FRAME_SOF1) {
            parser->type = 0u;
            parser->len = 0u;
            parser->index = 0u;
            parser->crc = 0u;
            parser->state = (uint8_t)FRAME_STATE_TYPE;
        } else if (byte == FRAME_SOF0) {
            /* 0xAA 0xAA 0x55：前一个 0xAA 不算起点，继续等 0x55 */
            parser->dropped_bytes++;
        } else {
            parser->dropped_bytes += 2u;
            parser->state = (uint8_t)FRAME_STATE_SOF0;
        }
        break;

    case FRAME_STATE_TYPE:
        parser->type = byte;
        parser->crc = crc8_update(0x00u, &byte, 1u);
        parser->state = (uint8_t)FRAME_STATE_LEN;
        break;

    case FRAME_STATE_LEN:
        if (byte > FRAME_MAX_PAYLOAD) {
            parser->oversize_count++;
            parser->dropped_bytes += 3u; /* 2 SOF + TYPE，LEN 本身也丢 */
            parser_reset(parser);
            return FRAME_EVENT_OVERSIZE;
        }
        parser->len = byte;
        parser->crc = crc8_update(parser->crc, &byte, 1u);
        if (byte == 0u) {
            parser->state = (uint8_t)FRAME_STATE_CRC;
        } else {
            parser->state = (uint8_t)FRAME_STATE_PAYLOAD;
        }
        break;

    case FRAME_STATE_PAYLOAD:
        parser->payload[parser->index] = byte;
        parser->crc = crc8_update(parser->crc, &byte, 1u);
        parser->index++;
        if (parser->index >= parser->len) {
            parser->state = (uint8_t)FRAME_STATE_CRC;
        }
        break;

    case FRAME_STATE_CRC:
    default:
        if (byte != parser->crc) {
            parser->bad_crc_count++;
            parser_reset(parser);
            return FRAME_EVENT_BAD_CRC;
        }
        out->type = parser->type;
        out->len = parser->len;
        if (parser->len > 0u) {
            memcpy(out->payload, parser->payload, parser->len);
        }
        parser_reset(parser);
        return FRAME_EVENT_READY;
    }

    return FRAME_EVENT_NONE;
}

size_t frame_encode(uint8_t type, const uint8_t *payload, uint8_t len,
                    uint8_t *out, size_t out_cap)
{
    size_t total;
    size_t offset;

    if (out == NULL) {
        return 0u;
    }
    if (len > FRAME_MAX_PAYLOAD) {
        return 0u;
    }
    if (len > 0u && payload == NULL) {
        return 0u;
    }

    total = (size_t)len + FRAME_OVERHEAD;
    if (out_cap < total) {
        return 0u;
    }

    out[0] = FRAME_SOF0;
    out[1] = FRAME_SOF1;
    out[2] = type;
    out[3] = len;
    offset = 4u;
    if (len > 0u) {
        memcpy(&out[offset], payload, len);
        offset += len;
    }
    out[offset] = crc8_update(0x00u, &out[2], (size_t)len + 2u); /* TYPE + LEN + PAYLOAD */
    return total;
}
