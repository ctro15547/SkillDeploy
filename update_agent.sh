#!/bin/bash

# 升级 OpenCode 和 Claude Code 的交互脚本
# 用途：检查并升级 npm 全局安装的 opencode 和 claude-code

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# 检查 npm 是否安装
check_npm() {
    if ! command -v npm &> /dev/null; then
        print_error "npm 未安装，请先安装 Node.js 和 npm"
        exit 1
    fi
    print_success "npm 已安装"
}

# 检查 bun 是否安装
check_bun() {
    if command -v bun &> /dev/null; then
        print_success "bun 已安装"
        return 0
    else
        return 1
    fi
}

# 检查是否在 sudo 环境中
check_sudo_env() {
    # 检查 SUDO_USER 环境变量，如果存在说明在 sudo 环境中
    if [ -n "$SUDO_USER" ]; then
        return 0  # 在 sudo 环境中
    else
        return 1  # 不在 sudo 环境中
    fi
}

# 检查是否有 sudo 权限（用于 npm 全局安装）
check_sudo_permission() {
    # 尝试执行一个无害的 sudo 命令，检查是否需要密码
    if sudo -n true 2>/dev/null; then
        return 0  # 有 sudo 权限，无需密码
    else
        return 1  # 没有 sudo 权限或需要密码
    fi
}

# 检查 opencode 是否安装（支持本地和 npm 安装）
check_opencode() {
    # 先检查本地安装
    if command -v opencode &> /dev/null; then
        opencode --version 2>/dev/null || echo "unknown"
    else
        # 再检查 npm 全局安装
        if npm list -g "opencode" &> /dev/null; then
            npm list -g "opencode" 2>/dev/null | grep "opencode" | head -1 | sed "s/.*@//"
        else
            echo ""
        fi
    fi
}

# 检查包是否全局安装
check_package() {
    local package=$1
    if npm list -g "$package" &> /dev/null; then
        local version=$(npm list -g "$package" 2>/dev/null | grep "$package" | head -1 | sed "s/.*@//")
        echo "$version"
    else
        echo ""
    fi
}

# 检查 bun 全局包
check_bun_package() {
    local package=$1
    if command -v bun &> /dev/null; then
        local version=$(bun list -g 2>/dev/null | grep "$package" | sed "s/.*@//")
        echo "$version"
    else
        echo ""
    fi
}

# 升级包
upgrade_package() {
    local package=$1
    local display_name=$2
    
    print_info "正在升级 $display_name..."
    
    # 检查权限
    if ! check_sudo_permission; then
        print_warning "可能需要 sudo 权限来升级全局包"
        read -p "是否使用 sudo 运行？(y/n): " use_sudo
        if [ "$use_sudo" = "y" ] || [ "$use_sudo" = "Y" ]; then
            if sudo npm install -g "$package@latest" 2>&1; then
                local new_version=$(npm list -g "$package" 2>/dev/null | grep "$package" | head -1 | sed "s/.*@//")
                print_success "$display_name 已升级到 $new_version"
                return 0
            else
                print_error "$display_name 升级失败"
                return 1
            fi
        else
            print_warning "已跳过升级"
            return 1
        fi
    else
        if npm install -g "$package@latest" 2>&1; then
            local new_version=$(npm list -g "$package" 2>/dev/null | grep "$package" | head -1 | sed "s/.*@//")
            print_success "$display_name 已升级到 $new_version"
            return 0
        else
            print_error "$display_name 升级失败"
            return 1
        fi
    fi
}

# 主菜单
show_menu() {
    echo ""
    echo -e "${BLUE}=== Agent 升级工具 ===${NC}"
    echo "1. 检查版本"
    echo -e "2. 升级 OpenCode                    ${YELLOW}(opencode upgrade)${NC}"
    echo -e "3. 升级 Oh-My-OpenCode (bun)        ${YELLOW}(bun add -g oh-my-opencode@latest)${NC}"
    echo -e "4. 升级 Claude Code                 ${YELLOW}(npm install -g @anthropic-ai/claude-code@latest)${NC}"
    echo "5. 升级全部"
    echo "6. 退出"
    echo ""
}

# 检查版本
check_versions() {
    echo ""
    print_info "检查已安装的包版本..."
    
    local opencode_version=$(check_opencode)
    local oh_my_opencode_version=$(check_bun_package "oh-my-opencode")
    local claude_code_version=$(check_package "@anthropic-ai/claude-code")
    
    if [ -z "$opencode_version" ]; then
        print_warning "OpenCode 未安装"
    else
        print_success "OpenCode 版本: $opencode_version"
    fi
    
    if [ -z "$oh_my_opencode_version" ]; then
        print_warning "Oh-My-OpenCode (bun) 未安装"
    else
        print_success "Oh-My-OpenCode 版本: $oh_my_opencode_version"
    fi
    
    if [ -z "$claude_code_version" ]; then
        print_warning "Claude Code 未安装"
    else
        print_success "Claude Code 版本: $claude_code_version"
    fi
}

# 主程序
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║   OpenCode & Claude Code 升级工具      ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # 检查 npm
    check_npm
    echo ""
    
    # 检查并显示 sudo 环境状态
    if check_sudo_env; then
        print_success "当前在 sudo 环境中运行"
    else
        print_warning "当前未在 sudo 环境中运行"
    fi
    echo ""
    
    # 检查权限提示
    if ! check_sudo_permission; then
        print_warning "提示：升级全局包可能需要 sudo 权限"
        print_info "如果升级失败，脚本会提示您使用 sudo"
        echo ""
    fi
    
    # 主循环
    while true; do
        show_menu
        read -p "请选择操作 (1-6): " choice
        
        case $choice in
            1)
                check_versions
                ;;
            2)
                print_info "升级 OpenCode..."
                if command -v opencode &> /dev/null; then
                    # 使用 opencode 自带的升级命令
                    if opencode upgrade 2>&1; then
                        print_success "OpenCode 升级完成"
                    else
                        print_error "OpenCode 升级失败，尝试使用 npm..."
                        upgrade_package "opencode" "OpenCode"
                    fi
                else
                    # 如果没有 opencode 命令，使用 npm 升级
                    upgrade_package "opencode" "OpenCode"
                fi
                ;;
            3)
                print_info "升级 Oh-My-OpenCode (bun)..."
                if command -v bun &> /dev/null; then
                    if bun add -g oh-my-opencode@latest 2>&1; then
                        local new_version=$(check_bun_package "oh-my-opencode")
                        print_success "Oh-My-OpenCode 已升级到 $new_version"
                    else
                        print_error "Oh-My-OpenCode 升级失败"
                    fi
                else
                    print_error "bun 未安装，无法升级 Oh-My-OpenCode"
                fi
                ;;
            4)
                print_info "升级 Claude Code..."
                if upgrade_package "@anthropic-ai/claude-code" "Claude Code"; then
                    print_success "Claude Code 升级完成"
                fi
                ;;
            5)
                print_info "升级所有包..."
                echo ""
                
                # 升级 OpenCode
                if command -v opencode &> /dev/null; then
                    print_info "使用 opencode upgrade 命令升级..."
                    if opencode upgrade 2>&1; then
                        print_success "OpenCode 升级完成"
                    else
                        print_warning "OpenCode 升级失败"
                    fi
                else
                    opencode_version=$(check_package "opencode")
                    if [ -n "$opencode_version" ]; then
                        upgrade_package "opencode" "OpenCode"
                    else
                        print_warning "OpenCode 未安装，跳过"
                    fi
                fi
                
                echo ""
                
                # 升级 Oh-My-OpenCode
                if command -v bun &> /dev/null; then
                    oh_my_opencode_version=$(check_bun_package "oh-my-opencode")
                    if [ -n "$oh_my_opencode_version" ]; then
                        print_info "升级 Oh-My-OpenCode..."
                        if bun add -g oh-my-opencode@latest 2>&1; then
                            local new_version=$(check_bun_package "oh-my-opencode")
                            print_success "Oh-My-OpenCode 已升级到 $new_version"
                        else
                            print_warning "Oh-My-OpenCode 升级失败"
                        fi
                    else
                        print_warning "Oh-My-OpenCode 未安装，跳过"
                    fi
                else
                    print_warning "bun 未安装，跳过 Oh-My-OpenCode"
                fi
                
                echo ""
                
                # 升级 Claude Code
                claude_code_version=$(check_package "@anthropic-ai/claude-code")
                if [ -n "$claude_code_version" ]; then
                    upgrade_package "@anthropic-ai/claude-code" "Claude Code"
                else
                    print_warning "Claude Code 未安装，跳过"
                fi
                
                echo ""
                print_success "所有包升级完成"
                ;;
            6)
                print_info "退出程序"
                exit 0
                ;;
            *)
                print_error "无效的选择，请重试"
                ;;
        esac
    done
}

# 运行主程序
main
