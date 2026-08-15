# TeamUp 品牌头像与生成素材规范

> Status: Proposed<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B（仅审查合规与发布风险）<br>
> Last Updated: 2026-08-15

## 1. 用途与边界

本文是 TeamUp 小程序头像的唯一生成与验收说明。头像用于微信小程序后台的“小程序头像”，不是用户头像、广告素材或竞赛海报。

视觉目标是让高校学生在 144px 的小尺寸下快速识别“连接、组队、共同推进”，同时与当前小程序的克制、清晰的平台语言一致。最终选用的图片、生成工具、提示词版本和使用日期必须记录在本文件第 6 节，避免来源不明或重复生成后无法追溯。

已参考：

| Source | Principle | TeamUp adaptation | Boundary |
| --- | --- | --- | --- |
| <https://detail.design/detail/respect-platform-language> | 采用用户熟悉且克制的平台视觉语言 | 使用清晰轮廓、有限颜色和高辨识度图形 | 不复制任何现成品牌或界面 |
| <https://detail.design/detail/visual-alignment-for-buttons-with-icon> | 小尺寸图形需保持稳定的视觉居中与留白 | 图形居中，四周至少保留 15% 空白 | 不在头像中塞入操作图标或说明文字 |
| <https://detail.design/detail/describe-link-action> | 视觉元素服务于明确含义 | 用“互联路径”表达组队和协作 | 不把抽象图形解释为未经确认的产品功能 |

## 2. 已知视觉约束

- 当前小程序主色为深绿 `#12664F`，页面背景为浅灰绿 `#F6F8F7`，正文为深色 `#17231E`；头像可使用深绿加一个暖色强调，但不得依赖渐变或低对比细节。
- 输出应为 1:1 正方形 PNG。先生成 1024px 源图，最终裁切或缩放为 144px x 144px，文件小于 2MB。
- 头像不包含文字、字母、二维码、校徽、微信/QQ/Tencent 标志、人物肖像、手势、商业品牌、版权角色或水印。
- 图形必须原创。生成后应进行反向图片检索；若与已有品牌高度相似，直接废弃。
- 若生成工具的条款不允许商业使用、要求署名或不能保证使用权，不得作为正式头像。

## 3. 首选生成提示词

将以下内容整体复制到图像生成工具中。选择支持“透明背景”的工具时，必须同时开启透明背景输出。

```text
Use case: logo-brand
Asset type: WeChat Mini Program avatar for a university student team-formation platform
Primary request: an original abstract symbol named only by its visual idea,
"interlocking paths". Two equal, rounded geometric paths meet and support each other,
forming one compact upward-moving shape. It communicates two students becoming a project
team and moving forward together.
Scene/backdrop: genuinely transparent background
Style/medium: flat, vector-like logo mark; simple, scalable, calm and trustworthy
Composition/framing: one centered symbol in a square canvas; preserve at least 15% clear margin on every side; strong silhouette that remains recognizable at 44px and 144px
Color palette: deep green #12664F as the primary color, restrained warm amber #D6953B as a small secondary accent, no other dominant colors
Materials/textures: solid fills only, no texture
Text (verbatim): no text
Constraints: original design only; balanced negative space; high contrast; no gradients; no
shadow; no mockup; no 3D; no faces; no hands; no letters; no university crests; no WeChat,
QQ, Tencent, or other brand marks; no watermark
Avoid: chat bubble, handshake, generic human silhouette, puzzle piece, crowded details, thin lines, copied logo style
```

## 4. 备选提示词

仅在首选方向不满足第 5 节验收时使用其中一个备选方向。一次只生成一个方向，避免把多个概念混成一个图形。

### 4.1 伙伴节点

```text
Use case: logo-brand
Asset type: WeChat Mini Program avatar
Primary request: an original minimal mark made from two equal solid nodes and one shared connecting arc, expressing two peers forming a dependable project connection
Scene/backdrop: genuinely transparent background
Style/medium: flat, vector-like symbol with a bold silhouette
Composition/framing: centered square mark with generous clear margin; readable at 44px
Color palette: deep green #12664F with one small warm amber #D6953B accent
Text (verbatim): no text
Constraints: original only; no gradients, shadow, mockup, 3D, watermark, letters, faces,
hands, chat bubbles, third-party logos, or university crests
```

### 4.2 共同成长

```text
Use case: logo-brand
Asset type: WeChat Mini Program avatar
Primary request: an original compact abstract mark where two rounded forms join at a shared
base and subtly rise upward, expressing collaboration, mutual support, and project progress
Scene/backdrop: genuinely transparent background
Style/medium: flat, vector-like logo mark; calm, reliable, youth-oriented
Composition/framing: centered in a square with at least 15% margin; strong simple silhouette at 44px
Color palette: deep green #12664F, small warm amber #D6953B accent, transparent background
Text (verbatim): no text
Constraints: no gradients, no fine lines, no shadow, no 3D, no mockup, no text, no faces,
no hands, no puzzle pieces, no watermarks, no copied or third-party brand elements
```

## 5. 生成与提交步骤

1. 使用第 3 节生成 4 个候选图；每个候选只保留一个完整中心图形。
2. 在白色、浅灰绿 `#F6F8F7` 和深绿 `#12664F` 背景上预览，确保边缘和主图形都清楚。
3. 将候选缩小至 144px x 144px；若细线、空洞或强调色消失，则淘汰。
4. 对入选图进行反向图片检索，并确认生成工具条款允许本项目预期的商业使用。
5. 导出为小于 2MB 的 PNG；在微信小程序后台上传后，检查方形和圆形预览均无裁切问题。
6. 角色 A 确认最终候选后，填写第 6 节，并将本文状态改为 `Confirmed`。未确认前不得将候选图加入小程序代码或用于商业宣传。

## 6. 最终资产登记

当前状态：`TBD`，尚未生成或选择正式头像。

| Field | Value |
| --- | --- |
| Final file | `TBD` |
| Source file dimensions | `TBD` |
| Final uploaded dimensions / size | `TBD` |
| Generation tool and model | `TBD` |
| Prompt section / version | `TBD` |
| Generation date | `TBD` |
| Commercial-use terms checked by | `TBD` |
| Reverse-image check date / result | `TBD` |
| Role A approval | `TBD` |
