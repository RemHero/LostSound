# 音乐人声检测工具
# 简介
本项目用于对音乐歌曲中的人声进行检测、分离，建立在其他VAD(voice activity detection)框架的基础上，并进行适配性的整合、改写。相较于市面上其他同类检测工具，本项目具有更高的准确度，能满足某些用户的更高要求。
## 应用场景
本项目的本质是VAD，即voice activity detection；简单来说，VAD的作用就是从一段音频中标识出语音片段与非语音片段。 VAD在语音信号处理中有着广泛的应用，例如：语音增强，语音识别等。
在实际部署中，本项目的输入为一段音频或者音乐。音频会被划分为一连串的10ms区间，然后本项目会对每个10ms区间进行人声检测，并给出该区间内人声存在的概率(数值大小介于0~1)。
## 部署环境
+ 1. 编程语言：python 3.8.5
+ 2. 所需python包(pip install xxx):
> 1. numpy
> 2. scipy
> 3. matplotlib
> 4. webrtcvad

## 参考资料
|框架/项目名称|访问地址|备注|
|------|-----|----|
|VAD-python| https://github.com/marsbroshok/VAD-python |传统VAD算法，基于能量比 |
|spleeter| https://github.com/deezer/spleeter/tree/master/spleeter |人声、背景音分离工具|
|py-webrtcvad| https://github.com/wiseman/py-webrtcvad |基于AI的VAD算法|

# 效果
## 测试方法
将50首歌曲输入到本项目中，然后将本项目的检测结果与标准答案进行比照，通过AUC评价指标判别准确性。
为了更好地体现模型竞争力，我们还额外测试了其他两个VAD模型：VAD-python和py-webrtcvad，以供对比。

## 测试结果
|测试对象|AUC得分|
|-----|------|
|本项目|0.8062|
|py webrtcvad|0.5974|
|VAD-python|0.5257|

由以上结果可知，本项目在人声检测的准确度方面优势明显。