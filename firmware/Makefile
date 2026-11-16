# firmware/Makefile
#
# 一条命令验证逻辑层，不需要板子、不需要打开 Keil：
#
#   make test     # host 编译 app/ 层并跑单元测试（秒级，CI 同款）
#   make clean
#
# 交叉编译目标（.elf + size 报告）等 platform/ 由 CubeMX 生成后在这里补，
# 现在不写空壳配方 —— 一个跑不通的 target 比没有 target 更容易骗到自己。
#
# 之所以能在 PC 上编译 app/，是因为 app/ 不 include 任何 HAL 头文件。
# 这条依赖规则由本文件的 -I 路径强制：host 编译时根本没有 HAL 的 include 路径。

HOST_CC ?= cc
BUILD_DIR := build
HOST_BIN := $(BUILD_DIR)/host_tests

# -Werror：警告即错误。现在只有一个模块，成本为零；等两千行再开就开不动了。
WARN := -Wall -Wextra -Wpedantic -Wshadow -Wstrict-prototypes
HOST_CFLAGS := -std=c99 -O1 -g $(WARN) -Werror -Iapp -Itests

APP_SRC := $(wildcard app/*/*.c)
TEST_SRC := $(wildcard tests/*.c)

.PHONY: all test clean help

all: test

test: $(HOST_BIN)
	@./$(HOST_BIN)

$(HOST_BIN): $(APP_SRC) $(TEST_SRC) $(wildcard app/*/*.h) $(wildcard tests/*.h)
	@mkdir -p $(BUILD_DIR)
	$(HOST_CC) $(HOST_CFLAGS) $(APP_SRC) $(TEST_SRC) -o $@

clean:
	rm -rf $(BUILD_DIR)

help:
	@echo "make test    编译并运行 host 端单元测试"
	@echo "make clean   删除 build/"
