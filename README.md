# iGuge Social Publisher

面向 Codex 的 iGuge healthy Facebook / LinkedIn 社媒发布技能。从官网选品，生成有来源的英文文案与四宫格图片，完成发布核验和 Google Sheets 记录。无站内文章发布。

## 使用

将本仓库放到 `~/.codex/skills/iguge-social-publisher/`，在 Codex 中使用：

- `使用 $iguge-social-publisher，随机选择一个产品并发布一次。`
- `使用 $iguge-social-publisher，为指定产品生成 dry-run 草稿。`
- `使用 $iguge-social-publisher，续跑指定 manifest 中未完成的步骤。`

运行前安装 Python 3.10+ 和 `requirements.txt` 中的依赖。图片生成使用 Codex 内置 imagegen；实际发布需要对目标主页的有效管理权限及支持上传的浏览器或连接器。Google Sheets 记录需要既有表格写入权限。

## 固定目标

- 产品：https://www.igugehealthy.com/products/
- Facebook：https://www.facebook.com/profile.php?id=61595573086492
- LinkedIn：https://www.linkedin.com/company/144048448/admin/dashboard/

该技能为上述品牌账号维护，不能在未知身份或个人账号下代发。Google Sheets 目标见 `references/reporting.md`；表格 ID 是资源定位符，不提供访问权限。

## 行为约束

- 全量分页后随机选择，最多审核十个候选；指定产品不会擅自替换。
- 使用可核对的剂型、原料、MOQ 等信息，不把模板定制选项或功效描述变成承诺。
- 发布前审查最终图片和文案；任何提交开始后保留状态，结果不明先核对，不重复发布。
- dry-run 不发帖、不写在线表格；本技能不自行创建定时任务。
- 运行素材和证据保留在技能目录以外，不提交到本仓库。

完整流程见 [SKILL.md](SKILL.md)。

## 本地检查

```bash
python3 -m pip install -r requirements.txt
python3 scripts/test_workflow.py
```

测试使用临时本地数据，不登录或提交社媒帖子。公开目录采集也不代表账号权限验证或发布成功。
