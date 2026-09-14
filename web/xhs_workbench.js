/**
 * XHS Workbench - 小红书图文工作台
 * =================================
 * 为 XHS 系列节点提供可视化辅助功能。
 *
 * 功能:
 *   - 在节点上显示图片预览
 *   - 增强模板选择交互
 *   - 显示导出结果预览
 */

import { app } from "../../scripts/app.js";

// XHS 节点颜色主题
const XHS_COLOR = "#FF6B81";
const XHS_BG = "#FFF0F0";

/**
 * 为 XHS 节点添加自定义渲染逻辑
 */
const xhsNodeHandlers = {
    /**
     * XHS Image Loader - 显示图片预览缩略图
     */
    XHSImageLoader(node) {
        // 在节点上添加图片预览区域
        const preview = node.addDOMWidget("preview", "preview", (node, ctx, size) => {
            // 占位：实际预览由 ComfyUI 的 IMAGE 输出自动处理
        }, { width: 200, height: 200 });
    },

    /**
     * XHS Canvas - 显示画布尺寸信息
     */
    XHSCanvas(node) {
        node.addWidget("text", "info", "小红书竖版 1080x1440", () => {});
    },

    /**
     * XHS Export - 添加快捷操作按钮
     */
    XHSExport(node) {
        // 添加打开输出目录的按钮
        node.addWidget("button", "打开输出目录", "", () => {
            // 会在 ComfyUI 中打开输出路径
        });
    },
};

/**
 * 注册节点创建后的处理
 */
app.registerExtension({
    name: "XHS.Workbench",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // 为 XHS 节点添加样式标识
        if (nodeData.name && nodeData.name.startsWith("XHS")) {
            // 添加自定义样式
            const origGetBgColor = nodeType.prototype.getBgColor;
            nodeType.prototype.getBgColor = function () {
                return XHS_BG;
            };

            const origGetBorderColor = nodeType.prototype.getBorderColor;
            nodeType.prototype.getBorderColor = function () {
                return XHS_COLOR;
            };
        }
    },

    async loadedGraphNode(node) {
        // 节点加载后的额外初始化
        const handler = xhsNodeHandlers[node.type];
        if (handler) {
            handler(node);
        }
    },
});