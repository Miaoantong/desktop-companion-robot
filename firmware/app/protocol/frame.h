/* frame.h — 定长帧 + CRC8 的编解码（纯逻辑，可在 PC 上测试）
 *
 * 线格式（共 5 + N 字节）：
 *
 *   +------+------+-------+------+-------------+-------+
 *   | 0xAA | 0x55 | TYPE  | LEN  | PAYLOAD[N]  | CRC8  |
 *   +------+------+-------+------+-------------+-------+
 *                        |<---- CRC 覆盖范围 ---->|
 *
 * 设计取舍：
 * - 双字节 SOF（0xAA 0x55）而非单字节：单字节 SOF 一旦出现在 payload 里，
 *   解析器就会频繁误同步。双字节把误同步概率降到 1/65536。
 * - LEN 是 1 字节且上限 32：协议用于状态上报与命令，不需要长包；
 *   小上限让解析器的栈/RAM 占用可静态预算（frame_parser_t ≈ 44 字节）。
 * - 接收是**逐字节状态机**，不是"收满一包再解析"：串口中断里来一个字节喂一次，
 *   没有额外缓冲，也不需要知道一帧何时结束。
 * - CRC 不通过时直接丢帧、不回 NACK：靠上层超时重发，避免 NACK 风暴。
 *
 * 本文件不 include 任何 HAL / CMSIS 头文件。
 */
#ifndef APP_PROTOCOL_FRAME_H
#define APP_PROTOCOL_FRAME_H

#include <stddef.h>
#include <stdint.h>

#include "protocol/crc8.h"

#define FRAME_SOF0        0xAAu
#define FRAME_SOF1        0x55u
#define FRAME_MAX_PAYLOAD 32u
#define FRAME_OVERHEAD    5u                              /* 2 SOF + TYPE + LEN + CRC */
#define FRAME_MAX_SIZE    (FRAME_MAX_PAYLOAD + FRAME_OVERHEAD)

/* 帧类型：先只定两三个真会用到的，其余等有需求再加，不预留假接口。 */
#define FRAME_TYPE_STATUS  0x01u /* L0 → L1：状态槽、传感器快照 */
#define FRAME_TYPE_CMD     0x02u /* L1 → L0：表情/动作命令 */
#define FRAME_TYPE_HEARTBEAT 0x03u /* 双向：慢脑存活证明，超时即降级 */

typedef struct {
    uint8_t type;
    uint8_t len;
    uint8_t payload[FRAME_MAX_PAYLOAD];
} frame_t;

typedef enum {
    FRAME_EVENT_NONE = 0,    /* 已消费 1 字节，帧尚未结束 */
    FRAME_EVENT_READY,       /* 收到完整且 CRC 正确的帧，out 已填充 */
    FRAME_EVENT_BAD_CRC,     /* 帧结构完整但校验失败，已丢弃并复位 */
    FRAME_EVENT_OVERSIZE     /* LEN 超过 FRAME_MAX_PAYLOAD，已丢弃并复位 */
} frame_event_t;

typedef struct {
    uint8_t state;              /* frame_state_t，用 uint8_t 存以固定结构体大小 */
    uint8_t type;
    uint8_t len;
    uint8_t index;
    uint8_t crc;                /* 运行中的 CRC，边收边算 */
    uint8_t payload[FRAME_MAX_PAYLOAD];
    uint32_t dropped_bytes;     /* 诊断：被丢弃的字节数（近似，用于算误帧率） */
    uint32_t bad_crc_count;
    uint32_t oversize_count;
} frame_parser_t;

void frame_parser_init(frame_parser_t *parser);

/* 丢弃当前半截帧、回到等 SOF 的状态，**不清空统计计数**。
 *
 * 上层必须在"字节间隔超时"（比如 20ms 没有新字节）时调用它：
 * 逐字节状态机在收到半截帧后会卡在帧中间，此时下一帧的 0xAA 0x55
 * 会被当成 TYPE/LEN 吃掉，症状是"偶发丢一整帧"。这是字节流解析的
 * 经典陷阱，解药不是更聪明的解析器，而是超时复位。 */
void frame_parser_reset(frame_parser_t *parser);

/* 喂一个字节。返回 FRAME_EVENT_READY 时 out 有效；其余情况 out 不被修改。
 * 每次调用最多产生一个事件，不阻塞、不动态分配。 */
frame_event_t frame_parser_push(frame_parser_t *parser, uint8_t byte, frame_t *out);

/* 编码一帧到 out（容量 out_cap）。
 * 返回写入的字节数；参数非法或容量不足返回 0。 */
size_t frame_encode(uint8_t type, const uint8_t *payload, uint8_t len,
                    uint8_t *out, size_t out_cap);

#endif /* APP_PROTOCOL_FRAME_H */
