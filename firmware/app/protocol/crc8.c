#include "protocol/crc8.h"

uint8_t crc8_update(uint8_t crc, const uint8_t *data, size_t len)
{
    size_t i;
    uint8_t bit;

    if (data == NULL) {
        return crc;
    }

    for (i = 0u; i < len; i++) {
        crc ^= data[i];
        for (bit = 0u; bit < 8u; bit++) {
            if ((crc & 0x80u) != 0u) {
                crc = (uint8_t)((crc << 1) ^ 0x07u);
            } else {
                crc = (uint8_t)(crc << 1);
            }
        }
    }
    return crc;
}

uint8_t crc8(const uint8_t *data, size_t len)
{
    return crc8_update(0x00u, data, len);
}
