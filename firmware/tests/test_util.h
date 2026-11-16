/* test_util.h — 极简断言框架（无第三方依赖，CI 与本地同一套）
 *
 * 为什么不用 Unity / CMock：C1 阶段只有两个被测模块，
 * 一个头文件足够；引第三方框架要维护 submodule 和构建配置，
 * 属于"看起来专业"而不是"真的有用"。
 * 测试数量超过 ~200 个或需要 mock 时再换 Unity，届时改动只在本文件。
 *
 * 输出用 ASCII：Windows 控制台默认 GBK 代码页，中文断言信息会乱码。
 */
#ifndef TESTS_TEST_UTIL_H
#define TESTS_TEST_UTIL_H

#include <stdio.h>

extern int g_checks;
extern int g_failures;

#define CHECK(cond)                                                          \
    do {                                                                     \
        g_checks++;                                                          \
        if (!(cond)) {                                                       \
            g_failures++;                                                    \
            printf("    FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);        \
        }                                                                    \
    } while (0)

#define CHECK_EQ(actual, expected)                                           \
    do {                                                                     \
        long a_ = (long)(actual);                                            \
        long e_ = (long)(expected);                                          \
        g_checks++;                                                          \
        if (a_ != e_) {                                                      \
            g_failures++;                                                    \
            printf("    FAIL %s:%d  %s == %ld, expected %ld\n",              \
                   __FILE__, __LINE__, #actual, a_, e_);                     \
        }                                                                    \
    } while (0)

#define RUN_SUITE(fn)                                                        \
    do {                                                                     \
        int before_ = g_failures;                                            \
        printf("[ RUN  ] %s\n", #fn);                                        \
        fn();                                                                \
        printf("[ %s ] %s\n", (g_failures == before_) ? " OK " : "FAIL", #fn); \
    } while (0)

#endif /* TESTS_TEST_UTIL_H */
