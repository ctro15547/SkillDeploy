#!/bin/bash

# 升级 OpenCode、Claude Code 和 Codex 的交互脚本
# 用途：检查并升级 npm/bun 全局安装的相关工具

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

# 检查 npm 全局目录是否可写（prefix 在用户目录下时无需 sudo）
check_npm_prefix() {
    NPM_PREFIX=$(npm config get prefix)
    print_info "npm 全局目录: $NPM_PREFIX"
    if [ -w "$NPM_PREFIX" ] && { [ ! -e "$NPM_PREFIX/lib/node_modules" ] || [ -w "$NPM_PREFIX/lib/node_modules" ]; }; then
        print_success "npm 全局目录可写，无需 sudo"
        return 0
    else
        print_error "npm 全局目录不可写，升级会失败"
        print_info "建议改为用户目录: npm config set prefix ~/.npm-global（并把 ~/.npm-global/bin 加入 PATH）"
        return 1
    fi
}

# 检查命令是否存在多个安装（例如 /usr/local 下残留的旧版本）
check_duplicates() {
    local cmd=$1
    local paths
    paths=$(which -a "$cmd" 2>/dev/null | awk '!seen[$0]++')
    if [ "$(echo "$paths" | grep -c .)" -gt 1 ]; then
        print_warning "$cmd 存在多个安装，实际生效的是第一个："
        echo "$paths" | sed 's/^/    /'
    fi
}

# 检查 opencode 是否安装
check_opencode() {
    check_package "opencode-ai"
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

    # 不使用 sudo：prefix 在用户目录下，用 sudo 会导致文件归 root 或装到别的目录
    if npm install -g "$package@latest" 2>&1; then
        local new_version=$(check_package "$package")
        print_success "$display_name 已升级到 $new_version"
        return 0
    else
        print_error "$display_name 升级失败（如报 EACCES，请检查 npm 全局目录权限）"
        return 1
    fi
}

# 升级 OpenCode
upgrade_opencode() {
    upgrade_package "opencode-ai" "OpenCode"
}

# 主菜单
show_menu() {
    echo ""
    echo -e "${BLUE}=== Agent 升级工具 ===${NC}"
    echo "1. 检查版本"
    echo -e "2. 升级 OpenCode                    ${YELLOW}(npm i -g opencode-ai)${NC}"
    echo -e "3. 升级 Oh-My-OpenCode (bun)        ${YELLOW}(bun add -g oh-my-opencode@latest)${NC}"
    echo -e "4. 升级 Claude Code                 ${YELLOW}(npm install -g @anthropic-ai/claude-code@latest)${NC}"
    echo -e "5. 升级 Codex                      ${YELLOW}(npm install -g @openai/codex@latest)${NC}"
    echo "6. 升级全部"
    echo "7. 退出"
    echo ""
}

# 检查版本
check_versions() {
    echo ""
    print_info "检查已安装的包版本..."
    
    local opencode_version=$(check_opencode)
    local oh_my_opencode_version=$(check_bun_package "oh-my-opencode")
    local claude_code_version=$(check_package "@anthropic-ai/claude-code")
    local codex_version=$(check_package "@openai/codex")
    
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

    if [ -z "$codex_version" ]; then
        print_warning "Codex 未安装"
    else
        print_success "Codex 版本: $codex_version"
    fi

    check_duplicates opencode
    check_duplicates claude
    check_duplicates codex
}

# 主程序
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║ OpenCode/Claude Code/Codex 升级工具    ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # 检查 npm
    check_npm
    echo ""
    
    # 不建议用 sudo 运行本脚本
    if [ -n "$SUDO_USER" ]; then
        print_warning "请不要用 sudo 运行本脚本，否则会使用 root 的 npm 配置"
    fi

    # 检查 npm 全局目录权限
    check_npm_prefix || true
    echo ""
    
    # 主循环
    while true; do
        show_menu
        read -p "请选择操作 (1-7): " choice
        
        case $choice in
            1)
                check_versions
                ;;
            2)
                print_info "升级 OpenCode..."
                if upgrade_opencode; then
                    print_success "OpenCode 升级完成"
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
                print_info "升级 Codex..."
                if upgrade_package "@openai/codex" "Codex"; then
                    print_success "Codex 升级完成"
                fi
                ;;
            6)
                print_info "升级所有包..."
                echo ""
                
                # 升级 OpenCode
                opencode_version=$(check_opencode)
                if [ -n "$opencode_version" ]; then
                    upgrade_opencode || true
                else
                    print_warning "OpenCode 未安装，跳过"
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
                    upgrade_package "@anthropic-ai/claude-code" "Claude Code" || true
                else
                    print_warning "Claude Code 未安装，跳过"
                fi

                echo ""

                # 升级 Codex
                codex_version=$(check_package "@openai/codex")
                if [ -n "$codex_version" ]; then
                    upgrade_package "@openai/codex" "Codex" || true
                else
                    print_warning "Codex 未安装，跳过"
                fi
                
                echo ""
                print_success "所有包升级完成"
                ;;
            7)
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
