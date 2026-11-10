# qianDao-photo-finder-skill

用于 **2026 届千岛湖自行车比赛**的 Agent Skill，支持 Codex 和 DeepSeek Harness。它按号码牌、骑行服和装备查找照片，并能逐张比较相册快照，找出需要复筛的新照片。

将 [`skills/qiandao-photo-finder`](skills/qiandao-photo-finder/SKILL.md) 复制到 Codex 的 skills 目录，然后在任务中调用 `$qiandao-photo-finder`。

在 **DeepSeek Harness** 中安装（将 `web` 换成自己的 profile）：

```sh
dsh plugin --profile web add github:bananaive/qianDao-photo-finder-skill
```

安装后在技能列表选择 `qiandao-photo-finder`，提供下述信息。插件只注册随包提供的技能及资源；照片读取、脚本执行和模型下载仍由当前会话按用户要求进行。包不包含安装时执行的脚本。支持 DSH 0.2.1-rc.2 及后续 0.2.x 版本（含 0.2.2 预发布版）；验证环境为 0.2.1-rc.2。

也可直接把 `skills/qiandao-photo-finder` 目录复制到 `~/.dsh/skills/`，由 Harness 的文件系统技能提供方发现。两种方式任选一种。

**必填参数：`live_album_url`**。传入本届赛事的图片直播链接；未提供时，Skill 会先向用户询问。仓库不预设相册链接。可同时提供号码牌、装备特征和想保留的拍摄角度。

示例（虚构链接及号码）：

> `$qiandao-photo-finder`：`live_album_url=https://example.com/event-photo-live`。帮我从正赛日相册找号码 0427 的清楚正面或侧面照片；如果已经有清单，只筛新增照片。

- **相册清单比对：** Python 3.10+，只使用标准库。
- **号码识别：** 可选 macOS 本地 Swift / Apple Vision 工具。
- **装备排序：** 可选 Pillow、PyTorch、Transformers 和本地 DINOv2 模型。输入为已定位的装备区域，输出待复核的排序。

这是由 Agent 执行的查找与复核流程，仍需提供可访问的相册页面或清单；不承诺任意直播站点均可自动抓取。遮挡或号码不可读的照片可能遗漏，候选需要人工确认。Windows/Linux 可使用清单比对和装备排序；附带的 Apple Vision OCR 脚本仅适用于 macOS。

开发验证：安装开发依赖后运行 `npm test`，检查技能在真实 DSH 注册表中的发现、资源读取和卸载；`npm pack --dry-run` 可检查分发文件。

读取直播相册需使用用户有权访问的页面、导出或 API。详见[清单格式](skills/qiandao-photo-finder/references/manifests.md)和[筛选与交付](skills/qiandao-photo-finder/references/review.md)。示例清单均为合成数据；请把实际照片、号码、账号和相册导出留在本地工作目录。

[MIT License](LICENSE)
