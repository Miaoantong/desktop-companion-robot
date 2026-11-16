/* main.c — host 端测试入口
 *
 * 这个文件能在 PC 上编译运行，是因为 app/ 层不 include 任何 HAL 头文件。
 * 这不是"顺便做出来的好事"，而是三层分层的**唯一验收标准**：
 * 哪天有人往 app/ 里塞了 stm32f1xx_hal.h，这条命令立刻编不过。
 */
#include <stdio.h>

#include "test_util.h"

int g_checks = 0;
int g_failures = 0;

void suite_crc8(void);
void suite_frame(void);

int main(void)
{
    /* 不打印 __DATE__ / __TIME__：它们会让构建不可复现，
     * 也没人需要知道测试二进制是什么时候编的（-Wdate-time 会直接报错）。 */
    printf("host tests\n\n");

    RUN_SUITE(suite_crc8);
    RUN_SUITE(suite_frame);

    printf("\n%d checks, %d failure(s)\n", g_checks, g_failures);
    if (g_failures == 0) {
        printf("RESULT: PASS\n");
        return 0;
    }
    printf("RESULT: FAIL\n");
    return 1;
}
