// ==UserScript==
// @name         yapi-extension
// @namespace    http://tampermonkey.net/
// @version      2024-07-24
// @description  复制body，生成kotlin/java/dart实体类
// @author       Aitsuki
// @match        https://yapi.lioncash.co/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=lioncash.co
// @grant        GM_registerMenuCommand
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function () {
    'use strict';

    const config = {
        codeType: GM_getValue('codeType', '0')
    };

    // 添加菜单项以打开配置对话框
    GM_registerMenuCommand('设置', openConfigDialog);

    function openConfigDialog() {
        // 创建对话框元素
        const dialog = document.createElement('dialog');
        dialog.innerHTML = `
            <form method="dialog">
                <h2>代码类型</h2>
                <label>
                    <input type="radio" name="option" value="0" ${config.codeType === '0' ? 'checked' : ''}>
                    Kotlin Moshi
                </label>
                <br>
                <label>
                    <input type="radio" name="option" value="1" ${config.codeType === '1' ? 'checked' : ''}>
                    Kotlin Gson
                </label>
                <br>
                <label>
                    <input type="radio" name="option" value="2" ${config.codeType === '2' ? 'checked' : ''}>
                    Dart json_serializable
                </label>
                <br>
                <menu>
                    <button id="saveButton" value="save">保存</button>
                    <button id="closeButton" value="cancel">取消</button>
                </menu>
            </form>
        `;
        document.body.appendChild(dialog);

        dialog.showModal();

        dialog.querySelector('#saveButton').addEventListener('click', () => {
            const codeType = dialog.querySelector('input[name="option"]:checked').value;
            GM_setValue('codeType', codeType);
            config.codeType = codeType;
            dialog.close();
            document.body.removeChild(dialog);
        });

        dialog.querySelector('#closeButton').addEventListener('click', () => {
            dialog.close();
            document.body.removeChild(dialog);
        });
    }

    function capitalize(str) {
        if (!str) return str;
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    function camel2snack(str) {
        return str.replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();
    }

    /**
     * @param {string} fieldname
     * @param {object} value 
     * @param {Map<string, string>} codes 
     * @returns {string}
     */
    function getKtFieldType(fieldname, value, codes) {
        let type = value.type.toLowerCase();
        if (type == "string") return "String?"
        if (type == "boolean") return "Boolean"
        if (type == "integer") return "Int"
        if (type == "long") return "Long"
        if (type == "number") {
            if (value.mock && value.mock.mock) {
                if (value.mock.mock == "@float") return "Double"
                if (value.mock.mock == "@Long") return "Long"
            } else {
                return "String?"
            }
        }
        if (type == "object") {
            let className = capitalize(fieldname)
            if (!codes.get(className)) {
                genCode(className, value, codes)
            }
            return className + "?"
        }
        if (type == "timezone" || type == "locale") return "String?"
        if (type == "array") {
            let itemType = value.items.type.toLowerCase();
            if (itemType == "string") return "List<String>?"
            if (itemType == "boolean") return "List<Boolean>?"
            if (itemType == "integer") return "List<Int>?"
            if (itemType == "long") return "List<Long>?"
            if (itemType == "number") {
                if (value.mock && value.mock.mock) {
                    if (value.mock.mock == "@float") return "List<Double>?"
                    if (value.mock.mock == "@Long") return "List<Long>?"
                } else {
                    return "List<Any>?"
                }
            }
            if (itemType == "object") {
                let className = capitalize(fieldname) + "Item"
                genCode(className, value.items, codes)
                return `List<${className}>?`
            }
            if (itemType == "timezone" || itemType == "locale") return "String?"
        }
        throw "unknown field type: " + fieldname
    }

        /**
     * @param {string} fieldname
     * @param {object} value 
     * @param {Map<string, string>} codes 
     * @returns {string}
     */
    function getDartFieldType(fieldname, value, codes) {
        let type = value.type.toLowerCase();
        if (type == "string") return "String?"
        if (type == "boolean") return "bool?"
        if (type == "integer") return "int?"
        if (type == "long") return "int?"
        if (type == "number") {
            if (value.mock && value.mock.mock) {
                if (value.mock.mock == "@float") return "double?"
                if (value.mock.mock == "@Long") return "int?"
            } else {
                return "num?"
            }
        }
        if (type == "object") {
            let className = capitalize(fieldname)
            if (!codes.get(className)) {
                genCode(className, value, codes)
            }
            return className + "?"
        }
        if (type == "timezone" || type == "locale") return "String?"
        if (type == "array") {
            let itemType = value.items.type.toLowerCase();
            if (itemType == "string") return "List<String>?"
            if (itemType == "boolean") return "List<bool>?"
            if (itemType == "integer") return "List<int>?"
            if (itemType == "long") return "List<int>>?"
            if (itemType == "number") {
                if (value.mock && value.mock.mock) {
                    if (value.mock.mock == "@float") return "List<double>?"
                    if (value.mock.mock == "@Long") return "List<int>?"
                } else {
                    return "List<num>?"
                }
            }
            if (itemType == "object") {
                let className = capitalize(fieldname) + "Item"
                genCode(className, value.items, codes)
                return `List<${className}>?`
            }
            if (itemType == "timezone" || itemType == "locale") return "String?"
        }
        throw "unknown field type: " + fieldname
    }


    /**
     * mystical(o_userGid) => ["mystical", "userGid"]
     * @param {string} key 
     * @returns {[string, string]}
     */
    function getFieldname(key) {
        const reg = /(\w+)\((\w+)\)/
        let matches = key.match(reg)
        if (matches) {
            return [matches[1], matches[2].substring(2)]
        } else {
            return [key, key]
        }
    }

    /**
     * 
     * @param {string} className 
     * @param {object} jsonschema 
     * @param {Map<string, string>} codes 
     * 
     */
    function genCode(className, jsonschema, codes) {
        let code = '';
        if (config.codeType === '0') { // Kotlin + Moshi
            code += `@JsonClass(generateAdapter = true)\n`
            code += `class ${className}(\n`
            for (const [key, value] of Object.entries(jsonschema.properties)) {
                let [obfname, name] = getFieldname(key)
                let type = getKtFieldType(name, value, codes)
                code += `    @Json(name = "${obfname}") val ${name}: ${type}, //${value.description}\n`
            }
            code += ")\n"
        } else if (config.codeType === '1') { // Kotlin + Gson
            code += `class ${className}(\n`
            for (const [key, value] of Object.entries(jsonschema.properties)) {
                let [obfname, name] = getFieldname(key)
                let type = getKtFieldType(name, value, codes)
                code += `    @SerializedName("${obfname}") val ${name}: ${type}, //${value.description}\n`
            }
            code += ")\n"
        } else if (config.codeType === '2') { // Dart + json_serializable
            code += `part '${camel2snack(className)}.g.dart';\n\n`
            code += `@JsonSerializable(createFactory: true, createToJson: true)\n`
            code += `class ${className} {\n`
            let fieldnames = []
            for (const [key, value] of Object.entries(jsonschema.properties)) {
                let [obfname, name] = getFieldname(key)
                fieldnames.push(name)
                let type = getDartFieldType(name, value, codes)
                code += `  //${value.description}\n`
                code += `  @JsonKey(name: "${obfname}")\n`
                code += `  final ${type} ${name};\n\n`
            }
            code += `  ${className}({\n`
            for (const name of fieldnames) {
                code += `    required this.${name},\n`
            }
            code += `  });\n\n`
            code += `  factory ${className}.fromJson(Map<String, dynamic> json) =>  _\$${className}FromJson(json);\n\n`
            code += `  Map<String, dynamic> toJson() => _\$${className}ToJson(this);\n`
            code += "}\n"
        }
        codes.set(className, code)
    }

    function showCodePanel(jsonschema) {
        let codes = new Map()
        genCode("ReqData", jsonschema, codes)
        let code = [...codes.values()].reverse().join("\n\n")

        // Create code panel element
        let codePanel = document.createElement('div');
        codePanel.id = "codePanel"
        codePanel.style.position = 'fixed';
        codePanel.style.top = '0';
        codePanel.style.left = '0';
        codePanel.style.width = '100%';
        codePanel.style.height = '100%';
        codePanel.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        codePanel.style.border = '1px solid #ccc';
        codePanel.style.padding = '10px';
        codePanel.style.zIndex = '9998';

        let codePanelContent = document.createElement('div');
        codePanelContent.style.position = 'absolute';
        codePanelContent.style.top = '50%';
        codePanelContent.style.left = '50%';
        codePanelContent.style.transform = 'translate(-50%, -50%)';
        codePanelContent.style.width = '80%';
        codePanelContent.style.height = '80%';
        codePanelContent.style.backgroundColor = '#fff';
        codePanelContent.style.border = '1px solid #ccc';
        codePanelContent.style.padding = '10px';
        codePanelContent.style.overflow = "auto"
        codePanelContent.innerHTML = `<pre><code class="language-javascript">${code.replaceAll("<", "&lt;").replaceAll(">", "&gt;")}</code></pre>`;
        Prism.highlightElement(codePanelContent.querySelector('code'));
        codePanel.appendChild(codePanelContent);
        document.body.appendChild(codePanel);

        codePanel.addEventListener('click', function (event) {
            if (event.target === codePanel) {
                document.body.removeChild(codePanel);
            }
        });
    }

    /**
     * @param {string} apiId 
     */
    async function getApiBodyData(apiId) {
        let url = "https://yapi.lioncash.co/api/interface/get?id=" + apiId
        let response = await fetch(url, {
            method: "GET", headers: {
                'Content-Type': 'application/json',
            }
        });
        return await response.json()
    }

    /**
     * @param {string} apiId 
     */
    function showButtons(apiId) {
        let oldButtons = document.querySelectorAll("h2.interface-title>button")
        for (const oldButton of oldButtons) {
            oldButton.parentNode.removeChild(oldButton)
        }

        let titles = document.querySelectorAll("h2.interface-title")
        for (const title of titles) {
            if (title.textContent == "请求参数") {
                let button = document.createElement("button")
                button.textContent = "Code"
                title.appendChild(button)
                button.addEventListener("click", async () => {
                    let data = await getApiBodyData(apiId)
                    showCodePanel(JSON.parse(data.data.req_body_other))
                })
            } else if (title.textContent == "返回数据") {
                let button = document.createElement("button")
                button.textContent = "Code"
                title.appendChild(button)
                button.addEventListener("click", async () => {
                    let data = await getApiBodyData(apiId)
                    showCodePanel(JSON.parse(data.data.res_body))
                })
            }
        }
    }

    function onRouterChanged() {
        let router = window.location.href
        console.log("onRouteChanged", router)
        let matchResult = router.match(/.+\/project\/(\d+)\/interface\/api\/(\d+)/);
        if (matchResult) {
            // let projectId = matchResult[1];
            let apiId = matchResult[2];
            console.log("apiId", apiId);
            onElementReady("div.caseContainer", () => {
                console.log("Element Ready");
                showButtons(apiId)
            })
        }
    }

    function onElementReady(selector, callback) {
        if (document.querySelector(selector)) {
            callback()
        } else {
            const observer = new MutationObserver((mutations, obs) => {
                if (document.querySelector(selector)) {
                    callback()
                    obs.disconnect()
                }
            });

            observer.observe(document, {
                childList: true,
                subtree: true
            });
        }
    }

    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = url;
        script.onload = callback;
        document.head.appendChild(script);
    }

    // Function to dynamically load a CSS file
    function loadCSS(url) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        document.head.appendChild(link);
    }

    window.onload = function () {
        loadScript("https://cdnjs.cloudflare.com/ajax/libs/prism/9000.0.1/prism.min.js")
        loadCSS("https://cdnjs.cloudflare.com/ajax/libs/prism/9000.0.1/themes/prism.min.css")
        let pushState = history.pushState;
        let replaceState = history.replaceState;
        history.pushState = function () {
            pushState.apply(history, arguments);
            onRouterChanged();
        };

        history.replaceState = function () {
            replaceState.apply(history, arguments);
            onRouterChanged();
        };

        window.addEventListener('popstate', onRouterChanged);
    };

    onRouterChanged()

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            let codePanel = document.getElementById("codePanel")
            if (codePanel) {
                event.preventDefault();
                document.body.removeChild(codePanel);
            }
        } else if (event.ctrlKey && event.key === 'a') {
            let codePanel = document.getElementById("codePanel")
            if (codePanel) {
                event.preventDefault();
                const codeElement = codePanel.querySelector("code")
                let range = document.createRange();
                range.selectNodeContents(codeElement);
                let selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }
    });
})();