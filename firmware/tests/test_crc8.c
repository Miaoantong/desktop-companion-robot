#include "test_util.h"

#include "protocol/crc8.h"

static void crc8_check_value(void)
{
    /* CRC-8/ATM 标准校验值：字符串 "123456789" → 0xF4。
     * 这个值能一眼看出多项式/初值/反射方向有没有写错。 */
    const uint8_t data[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
    CHECK_EQ(crc8(data, sizeof(data)), 0xF4);
}

static void crc8_empty(void)
{
    CHECK_EQ(crc8(NULL, 0u), 0x00);
    CHECK_EQ(crc8((const uint8_t *)"A", 0u), 0x00);
}

static void crc8_single_byte_known(void)
{
    /* 单字节 0x00：8 次移位全是 0，结果为 0x00 */
    const uint8_t zero = 0x00;
    CHECK_EQ(crc8(&zero, 1u), 0x00);
    /* 单字节 0x01 → 0x07（poly 在最高位溢出时的第一次异或） */
    const uint8_t one = 0x01;
    CHECK_EQ(crc8(&one, 1u), 0x07);
}

static void crc8_incremental_matches_oneshot(void)
{
    /* 边收边算必须等价于一次性算：串口中断里是一个字节一个字节喂的。 */
    const uint8_t data[] = "sensorless force estimation";
    uint8_t running = 0x00u;
    size_t i;

    for (i = 0u; i < sizeof(data) - 1u; i++) {
        running = crc8_update(running, &data[i], 1u);
    }
    CHECK_EQ(running, crc8(data, sizeof(data) - 1u));
}

static void crc8_detects_single_bit_flip(void)
{
    const uint8_t original[] = {0x01, 0x02, 0x03, 0x04};
    uint8_t flipped[4];
    size_t i;
    uint8_t base = crc8(original, sizeof(original));

    for (i = 0u; i < sizeof(original); i++) {
        size_t j;
        for (j = 0u; j < 4u; j++) {
            size_t k;
            for (k = 0u; k < sizeof(original); k++) {
                flipped[k] = original[k];
            }
            flipped[i] = (uint8_t)(flipped[i] ^ (uint8_t)(1u << j));
            CHECK(crc8(flipped, sizeof(flipped)) != base);
        }
    }
}

void suite_crc8(void)
{
    crc8_check_value();
    crc8_empty();
    crc8_single_byte_known();
    crc8_incremental_matches_oneshot();
    crc8_detects_single_bit_flip();
}
