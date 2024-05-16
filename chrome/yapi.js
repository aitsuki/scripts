// ==UserScript==
// @name         yapi-extension
// @namespace    http://tampermonkey.net/
// @version      2024-05-14
// @description  复制body，生成kotlin/java/dart实体类
// @author       Aitsuki
// @match        https://yapi.lioncash.co/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=lioncash.co
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    function capitalize(string) {
        if (!string) return string;
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    /**
     * @param {string} fieldname
     * @param {object} value 
     * @param {Map<string, string>} codes 
     * @returns {string}
     */
    function getFieldType(fieldname, value, codes) {
        if (value.type == "string") return "String?"
        if (value.type == "boolean") return "Boolean"
        if (value.type == "number") {
            if (value.mock && value.mock.mock) {
                if (value.mock.mock == "@float") return "Double"
                if (value.mock.mock == "@Long") return "Long"
            } else {
                return "String?"
            }
        }
        if (value.type == "object") {
            let className = capitalize(fieldname)
            if (!codes.get(className)) {
                jsonschema2Kotlin(className, value, codes)
            }
            return className + "?"
        }
        if (value.type == "array") {
            let type = value.items.type;
            if (type == "string") return "List<String>?"
            if (value.type == "boolean") return "List<Boolean>?"
            if (value.type == "number") {
                if (value.mock && value.mock.mock) {
                    if (value.mock.mock == "@float") return "List<Double>?"
                    if (value.mock.mock == "@Long") return "List<Long>?"
                } else {
                    return "List<Any>?"
                }
            }
            if (type == "object") {
                let className = capitalize(fieldname) + "Item"
                jsonschema2Kotlin(className, value.items, codes)
                return `List<${className}>?`
            }
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
    function jsonschema2Kotlin(className, jsonschema, codes) {
        let code = `class ${className}(\n`
        for (const [key, value] of Object.entries(jsonschema.properties)) {
            let [obfname, name] = getFieldname(key)
            let type = getFieldType(name, value, codes)
            code += `    @Json(name = "${obfname}") val ${name}: ${type}, //${value.description}\n`
        }
        code += ")\n"
        codes.set(className, code)
    }

    function showCodePanel(jsonschema) {
        let codes = new Map()
        jsonschema2Kotlin("Data", jsonschema, codes)
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
                    showCodePanel(JSON.parse(data.data.res_body).data)
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