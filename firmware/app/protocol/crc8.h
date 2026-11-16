/* crc8.h — CRC-8/ATM（poly 0x07, init 0x00, no reflect, xorout 0x00）
 *
 * 为什么不用查表：256 字节表在 F103 的 20KB RAM 里不划算，
 * 16 项半字节表要额外代码；帧长 ≤ 37 字节，逐位算不到 10µs，
 * 在 1kHz 环里完全可以接受。若将来帧变长或频率提高，再换半字节表。
 *
 * 本文件不 include 任何 HAL / CMSIS 头文件 —— 它必须能在 PC 上编译。
 */
#ifndef APP_PROTOCOL_CRC8_H
#define APP_PROTOCOL_CRC8_H

#include <stddef.h>
#include <stdint.h>

/* 增量计算：crc 传上一次的返回值，首次传 0x00。用于流式校验（边收边算）。 */
uint8_t crc8_update(uint8_t crc, const uint8_t *data, size_t len);

/* 一次性计算，等价于 crc8_update(0x00, data, len)。 */
uint8_t crc8(const uint8_t *data, size_t len);

#endif /* APP_PROTOCOL_CRC8_H */
