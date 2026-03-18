# MessageArray 消息数组

> 消息段的容器，链式构造、查询过滤。完整方法列表见 [reference/types/2_message_array.md](../../../reference/types/2_message_array.md)。

---

## 创建 MessageArray

```python
from ncatbot.types import MessageArray, PlainText, At

msg = MessageArray()                                   # 空数组
msg = MessageArray([PlainText(text="Hello"), At(user_id="123456")])  # 传入列表
msg = MessageArray.from_list([...])                    # 从 OB11 字典列表
msg = MessageArray.from_any("[CQ:at,qq=123456]Hello")  # 自动解析
```

---

## 链式构造

所有 `add_*` 方法返回 `self`，支持链式调用：

```python
msg = (
    MessageArray()
    .add_reply(12345)                              # 回复引用
    .add_at(123456)                                # @某人
    .add_text(" 你好！看看这张图 ")                   # 文本
    .add_image("https://example.com/img.png")       # 图片
    .add_video("https://example.com/video.mp4")     # 视频
)
```

常用方法：`add_text` / `add_image` / `add_video` / `add_at` / `add_at_all` / `add_reply` / `add_segment`

---

## 查询与过滤

```python
msg.text                     # 拼接所有纯文本段
msg.filter_text()            # [PlainText, ...]
msg.filter_image()           # [Image, ...]
msg.filter(Record)           # 按类型泛型过滤
msg.is_at(123456)            # 是否 @了指定用户
```

---

## 序列化

```python
data = msg.to_list()         # → OB11 字典列表
msg2 = MessageArray.from_list(data)
```

`MessageArray` 支持迭代、`len()`、`+` 拼接。

---

[← 上一篇：消息段参考](1_segments.md) | [返回目录](README.md) | [下一篇：QQ 合并转发 →](../qq/2_forward.md)
