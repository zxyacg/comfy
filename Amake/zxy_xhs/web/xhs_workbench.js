/**
 * XHS Workbench - 小红书图文工作台
 * =================================
 * 为 XHS 系列节点提供轻量可视化辅助。
 *
 * 设计原则:
 *   - 不使用 addDOMWidget（性能杀手，会导致面板卡顿）
 *   - 图片预览由 ComfyUI 的 IMAGE 输出自动处理
 *   - 样式通过 CSS class 注入，不覆盖原型方法
 *   - 节点信息通过轻量 widget 展示
 */

import { app } from "../../scripts/app.js";

const XHS_COLOR = "#FF6B81";
const XHS_BG = "#FFF0F0";

/**
 * 注入 XHS 节点样式 CSS（一次性，避免反复操作原型）
 */
function injectXhsStyles() {
    const styleId = "xhs-workbench-styles";
    if (document.getElementById(styleId)) return;

    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
        .xhs-node { border-color: ${XHS_COLOR} !important; }
        .xhs-node .node-bg { fill: ${XHS_BG}; }
    `;
    document.head.appendChild(style);
}

/**
 * 轻量级节点初始化处理器（不创建 DOM Widget）
 */
const xhsNodeHandlers = {
    XHSCanvas(node) {
        node.addWidget("text", "info", "小红书竖版 1080x1440", () => {});
    },
};

app.registerExtension({
    name: "XHS.Workbench",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name && nodeData.name.startsWith("XHS")) {
            injectXhsStyles();

            const origOnDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function (ctx) {
                ctx.strokeStyle = XHS_COLOR;
                ctx.fillStyle = XHS_BG;
                if (origOnDrawBackground) {
                    origOnDrawBackground.call(this, ctx);
                }
            };
        }
    },

    async loadedGraphNode(node) {
        const handler = xhsNodeHandlers[node.type];
        if (handler) {
            handler(node);
        }
    },
});