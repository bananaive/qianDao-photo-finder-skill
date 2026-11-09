# qianDao-photo-finder-skill

用于 **2026 届千岛湖自行车比赛**的 Codex Skill。它按号码牌、骑行服和装备查找照片，并能逐张比较相册快照，找出需要复筛的新照片。

将 [`skills/qiandao-photo-finder`](skills/qiandao-photo-finder/SKILL.md) 复制到 Codex 的 skills 目录，然后在任务中调用 `$qiandao-photo-finder`。

**必填参数：`live_album_url`**。传入本届赛事的图片直播链接；未提供时，Skill 会先向用户询问。仓库不预设相册链接。可同时提供号码牌、装备特征和想保留的拍摄角度。

示例（虚构链接及号码）：

> `$qiandao-photo-finder`：`live_album_url=https://example.com/event-photo-live`。帮我从正赛日相册找号码 0427 的清楚正面或侧面照片；如果已经有清单，只筛新增照片。

- **相册清单比对：** Python 3.10+，只使用标准库。
- **号码识别：** 可选 macOS 本地 Swift / Apple Vision 工具。
- **装备排序：** 可选 Pillow、PyTorch、Transformers 和本地 DINOv2 模型。输入为已定位的装备区域，输出待复核的排序。

读取直播相册需使用用户有权访问的页面、导出或 API。详见[清单格式](skills/qiandao-photo-finder/references/manifests.md)和[筛选与交付](skills/qiandao-photo-finder/references/review.md)。示例清单均为合成数据；请把实际照片、号码、账号和相册导出留在本地工作目录。

[MIT License](LICENSE)
