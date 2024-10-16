// 移除占位符函数
function removePlaceholder(elementId, placeholderText) {
    const element = document.getElementById(elementId);
    if (element.textContent.trim() === placeholderText) {
        element.textContent = "";  // 清空内容
        element.classList.remove("placeholder");
    }
}

// 设置占位符函数
function setPlaceholder(elementId, placeholderText) {
    const element = document.getElementById(elementId);
    if (element.textContent.trim() === "") {
        element.textContent = placeholderText;  // 设置占位符
        element.classList.add("placeholder");
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setPlaceholder('text-source', '在这里标记文字来源');
    setPlaceholder('title', '在这里填写标题');
    setPlaceholder('content', '在这里填写内容');
});

function downloadCard() {
    // 获取 exhibit 区域的 DOM 元素
    const card = document.querySelector('.exhibit');

    // 使用 html2canvas 将卡片内容渲染为图片
    html2canvas(card, {
        scale: 2,  // 提高分辨率，增加清晰度
        useCORS: true,  // 允许跨域处理图片
        allowTaint: true,  // 允许跨域渲染
        logging: true,  // 打印日志帮助调试
    }).then(canvas => {
        // 将 canvas 转换为图片数据
        const image = canvas.toDataURL('image/png');

        // 创建一个下载链接
        const link = document.createElement('a');
        link.href = image;
        link.download = 'card.png';  // 设置下载的文件名

        // 自动点击链接进行下载
        link.click();
    });
}
