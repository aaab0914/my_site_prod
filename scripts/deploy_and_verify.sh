#!/bin/bash
# ============================================================
# deploy_and_verify.sh
# 可复用部署脚本（保留在项目中）
# 用法: bash scripts/deploy_and_verify.sh "提交信息"
# 功能:
#   1. git 备份 (bundle)
#   2. git add + commit + push
#   3. docker compose up --build -d 重建
#   4. 等待容器健康
#   5. 验证网站路由
#   6. 验证 gallery 图片缓存头
# ============================================================
set -e
REPO="/var/www/my_site_prod_repo_new"
COMMIT_MSG="${1:-fix: auto deploy $(date +%Y%m%d_%H%M%S)}"

cd "$REPO"

echo "============================================================"
echo "1/7 git 状态"
git status -s || true

echo "============================================================"
echo "2/7 创建 git bundle 备份"
mkdir -p backups/git
git bundle create "backups/git/my_site_repo_$(date +%Y%m%d_%H%M%S).bundle" --all 2>&1 | tail -2 || true
ls -lh backups/git/ | tail -3

echo "============================================================"
echo "3/7 提交改动"
git add -A
if git diff --cached --quiet; then
    echo "(无改动可提交)"
else
    git commit -m "$COMMIT_MSG" || true
fi

echo "============================================================"
echo "4/7 推送到 GitHub"
git push origin master 2>&1 || echo "推送失败(网络或认证问题)"

echo "============================================================"
echo "5/7 重建容器"
docker compose -f docker-compose.prod.yml up --build -d 2>&1 | grep -E "Built|Started|Running|Recreated|error|Error" || true

echo "============================================================"
echo "6/7 等待容器健康"
for i in $(seq 1 30); do
    sleep 5
    if docker ps --format '{{.Names}} {{.Status}}' | grep my_site_prod_repo_new-web | grep -q healthy; then
        echo "  web 容器健康 (等待 $((i*5)) 秒)"
        break
    fi
    if [ "$i" -eq 30 ]; then echo "  WARNING: 容器未健康"; fi
done
echo "  健康容器数: $(docker ps --format '{{.Status}}' | grep -c healthy)"

echo "============================================================"
echo "7/7 验证"
for p in "/" "/blog/" "/blog/gallery/"; do
    code=$(curl -s -L -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080$p")
    if [ "$code" = "200" ]; then mark="[OK]"; else mark="[FAIL]"; fi
    echo "  $mark $p -> $code"
done
echo "--- 图片缓存头 ---"
curl -s -I "http://127.0.0.1:8080/blog/gallery/87/media/" | grep -iE "cache-control|http/|etag|last-modified" || echo "  (未找到缓存头)"
echo "============================================================"
echo "完成！"
