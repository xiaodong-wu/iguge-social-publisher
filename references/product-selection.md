# 全量选品与候选替换

从 `https://www.igugehealthy.com/products/` 遍历全部同站产品分页。
`/products/`、`/products/index.html` 和 `/products/1.html` 归一为同一首页；
不跟随带筛选查询参数的链接。只收录 `product-grid` 内 `product-card` 的详情链接，
当前产品详情为根路径下以数字标识结尾的 `.html` 页面。分类、导航、Blog 和页脚不入池。
完整遍历并按 URL 去重后才打乱，保留 `catalog.json` 的全部分页来源；十次上限约束
候选产品，不限制分页数。分页 404/410 单独记录，其他目录故障停止。

每次执行建立 `selection.json`。默认最多审核十个候选，指定产品只审核该产品；
用户明确允许替代时使用 `--allow-reselect`。不可重建台账绕过上限，独立新任务可以重复产品。

抓取器依照 iGuge 当前模板提取：

- `detail-copy` 中的 H1、`lead` 摘要、`detail-quick-facts`；
- `key-attributes-table` 中的产品属性；
- `pc-specs` 的 Format / MOQ / Project options，以及 `pc-ingredient-reference` 原料声明；
- `pc-overview-copy` 的产品介绍，排除 `pc-note` 通用引导；
- `product-gallery-main` 主图，以及 `gallery-thumbs` 图库链接，排除水印 logo；
- `breadcrumbs` 分类和 `add-quote` 的站内产品 ID。产品 ID 不是 SKU，不虚构型号。

官网部分 canonical 使用非 www 域名，脚本将同域 www / 非 www 统一为用户指定的
`https://www.igugehealthy.com` 并保留 `source_canonical_url`。不从旧 URL 的词语
推导功效、成分数量、浓度或剂量；URL slug 可能保留旧命名，以当前页面为准。

主图须可解码、短边至少 300 像素，至少三个可用规格。Format 的 powder/powders、
capsule/capsules 等明确单复数映射记为 `facts.variations`，不算冲突或独立佐证。
其他不同规格保留为冲突，需人工对照原文。不得把原料选项合并成默认成分表。

`discussion_sections` 保存 Formula、Sample、Packaging、FAQ 等讨论文本供语义辨别，
不计入产品证据；“discuss / explore / confirm”不是已经具备的配方、包材或测试结果。
`restricted_source_claims` 保存 Function 等功效字段，不计入可用规格和文案证据。
元描述、图片 alt、评论、通用工厂文案也不补足规格。原料、剂型、MOQ、适用对象、
保质期、服务能力的标题/摘要/表格/专属正文仍需人工互查，抓取成功不等于审核通过。

模板不识别时停止检查原始 HTML，不将解析器或网络故障当作十个不合格产品。
若人工发现产品专属证据问题且尚未开始任何提交：

```bash
python3 scripts/scrape_product.py --retry-from MANIFEST --reason "具体冲突及来源"
```

新候选沿用台账剩余预算及原 live/dry-run 模式，建立新运行目录并重做素材。
任何提交开始后（包括结果不明）禁止换品。文案格式、图片生成、网络、权限和工具问题
在原任务内处理，不能靠换品绕过。更多事实规则见 [内容规范](content-spec.md)。
