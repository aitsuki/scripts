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
  "use strict";

  /**
   * @typedef {Object} CodeType
   * @property {string} DART
   * @property {string} KOTLIN
   */

  /**
   * @typedef {Object} Config
   * @property {CodeType} codeType
   */

  /** @type {CodeType} */
  const CodeType = {
    DART: "dart",
    KOTLIN: "kotlin",
  };

  /** @type {Config} */
  const config = {
    codeType: GM_getValue("codeType", CodeType.DART),
  };

  // 添加菜单项以打开配置对话框
  GM_registerMenuCommand("设置", openConfigDialog);

  function openConfigDialog() {
    // 创建对话框元素
    const dialog = document.createElement("dialog");
    dialog.innerHTML = `
            <form method="dialog">
                <h2>代码类型</h2>
                <label>
                    <input type="radio" name="option" value="${
                      CodeType.DART
                    }" ${config.codeType === CodeType.DART ? "checked" : ""}>
                    Dart
                </label>
                <br>
                <label>
                    <input type="radio" name="option" value="${
                      CodeType.KOTLIN
                    }" ${config.codeType === CodeType.KOTLIN ? "checked" : ""}>
                    Kotlin
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

    dialog.querySelector("#saveButton").addEventListener("click", () => {
      const codeType = dialog.querySelector(
        'input[name="option"]:checked'
      ).value;
      GM_setValue("codeType", codeType);
      config.codeType = codeType;
      dialog.close();
      document.body.removeChild(dialog);
    });

    dialog.querySelector("#closeButton").addEventListener("click", () => {
      dialog.close();
      document.body.removeChild(dialog);
    });
  }

  class StringUtils {
    /**
     * 将字符串的首字母大写
     * @param {string} value
     * @returns {string}
     */
    static capitalizeFirstLetter(value) {
      return value.charAt(0).toUpperCase() + value.slice(1);
    }

    /**
     * 将驼峰字符串转成蛇形字符串
     * @param {string} value
     * @returns {string}
     */
    static camelToSnakeCase(value) {
      return value.replace(/([a-z])([A-Z])/g, "$1_$2").toLowerCase();
    }
  }

  /**
   * @typedef {Object} DataType
   * @property {string} STRING - "string"
   * @property {string} BOOLEAN - "boolean"
   * @property {string} NUMBER - "number"
   * @property {string} INTEGER - "integer"
   * @property {string} LONG - "long"
   * @property {string} FLOAT - "float"
   * @property {string} OBJECT - "object"
   * @property {string} ARRAY - "array"
   */

  /** @type {DataType} */
  const DataType = {
    STRING: "string",
    BOOLEAN: "boolean",
    NUMBER: "number",
    INTEGER: "integer",
    LONG: "long",
    FLOAT: "float",
    OBJECT: "object",
    ARRAY: "array",
  };

  /**
   * @typedef {Object} Property
   * @property {string} name
   * @property {string} obfuscateName
   * @property {DataType} type
   * @property {string} [description]
   * @property {Property|null} [items]
   * @property {Object.<string, Property>} [properties]
   */

  /**
   * @typedef {Object} Class
   * @property {string} name
   * @property {Object.<string, Property>} properties
   * @property {string} [description]
   */

  class SchemaParser {
    /**
     * Parse the schema and return a list of classes
     * @param {Object} schema - The schema to parse
     * @returns {Class[]}
     */
    static parse(schema) {
      const classes = [];
      if (schema.type == DataType.ARRAY) {
        schema = this._obtainObjectSchemaFromArray(schema);
      } else if (schema.title.startsWith("Response<")) {
        schema = this._obtainObjectSchemaResponse(schema);
      }
      const mainClass = {
        name: (schema.title || "MainClass").replace(/(?:VO|DTO)$/, ""),
        properties: {},
        description: schema.description || "",
      };

      for (const [key, data] of Object.entries(schema.properties || {})) {
        const prop = this._parseProperty(key, data);
        mainClass.properties[prop.name] = prop;
        classes.push(...this._extractNestedClasses(prop.name, prop));
      }

      classes.unshift(mainClass);
      return classes;
    }

    /**
     * @param {Object} arraySchema - Array schema
     * @returns {Object} - Object schema
     */
    static _obtainObjectSchemaFromArray(arraySchema) {
      const matches = (arraySchema.title || "").match(/List<(\w+)>/);
      const title = matches ? matches[1] : null;

      const schema = arraySchema.items;
      schema.title = title;
      schema.description = arraySchema.title;
      return schema;
    }

    /**
     * @param {Object} responseSchema - Response schema
     * @returns {Object} - Object schema
     */
    static _obtainObjectSchemaResponse(responseSchema) {
      const matches = (responseSchema.title || "").match(/Response<(\w+)>/);
      const title = matches ? matches[1] : null;

      const schema = responseSchema.properties.data;
      schema.title = title;
      return schema;
    }

    /**
     * @param {string} propName - The property name to parse
     * @returns {[string, string]} - [obfuscateName, name]
     */
    static _parsePropertyName(propName) {
      const pattern = /(\w+)\((\w+)\)/;
      const matches = propName.match(pattern);
      if (matches) {
        return [matches[1], matches[2].slice(2)];
      } else {
        return [propName, propName];
      }
    }

    /**
     * @param {string} key - The property key
     * @param {Object} data - The property data
     * @returns {Property}
     */
    static _parseProperty(key, data) {
      const [obfuscateName, name] = this._parsePropertyName(key);
      const propType = data.type || "string";
      const description = data.description || "";

      if (propType === DataType.ARRAY) {
        const items = this._parseProperty(`${name}Item`, data.items || {});
        return {
          name,
          obfuscateName,
          type: propType,
          description,
          items,
        };
      } else if (propType === DataType.OBJECT) {
        const properties = Object.fromEntries(
          Object.entries(data.properties || {}).map(([k, v]) => [
            k,
            this._parseProperty(k, v),
          ])
        );
        return {
          name,
          obfuscateName,
          type: propType,
          description,
          properties,
        };
      } else {
        let finalType = propType;
        if (propType === DataType.NUMBER) {
          const mockType = data.mock?.mock;
          if (mockType === "@float") {
            finalType = DataType.FLOAT;
          } else if (mockType === "@Long") {
            finalType = DataType.LONG;
          }
        }
        return {
          name,
          obfuscateName,
          type: finalType,
          description,
        };
      }
    }

    /**
     * @param {string} name
     * @param {Property} prop
     * @returns {Class[]}
     */
    static _extractNestedClasses(name, prop) {
      const classes = [];
      if (prop.type === DataType.OBJECT) {
        const newClass = {
          name: StringUtils.capitalizeFirstLetter(name),
          properties: prop.properties,
        };
        classes.push(newClass);
        for (const nestedProp of Object.values(prop.properties)) {
          classes.push(
            ...this._extractNestedClasses(
              `${StringUtils.capitalizeFirstLetter(
                name
              )}${StringUtils.capitalizeFirstLetter(nestedProp.name)}`,
              nestedProp
            )
          );
        }
      } else if (prop.type === DataType.ARRAY && prop.items) {
        classes.push(...this._extractNestedClasses(`${name}Item`, prop.items));
      }
      return classes;
    }
  }

  class CodeGenerator {
    /**
     * Generate dart classes
     * @param {Class[]} classes
     */
    static generateDartClasses(classes) {
      /**
       * @param {Property} prop
       * @returns {string} - 对应的dart类型
       */
      function convertToDartType(prop) {
        switch (prop.type) {
          case DataType.STRING:
            return "String";
          case DataType.BOOLEAN:
            return "bool";
          case DataType.NUMBER:
            return "double";
          case DataType.INTEGER:
          case DataType.LONG:
            return "int";
          case DataType.FLOAT:
            return "double";
          case DataType.OBJECT:
            return StringUtils.capitalizeFirstLetter(prop.name);
          case DataType.ARRAY:
            if (prop.items) {
              const itemType = convertToDartType(prop.items);
              return `List<${itemType}>`;
            } else {
              return `List<dynamic>`;
            }
          default:
            return "dynamic";
        }
      }

      /**
       * Generate Dart property
       * @param {Property} prop - The property
       * @returns {string} - The generated Dart property
       */
      function generateProperty(prop) {
        let type = convertToDartType(prop);
        const description = prop.description
          ? `  /// ${prop.description}\n`
          : "";
        return `${description}  @JsonKey(name: '${prop.obfuscateName}')\n  final ${type}? ${prop.name};\n`;
      }

      /**
       * Generate Dart class
       * @param {Class} cls - The class
       * @returns {string} - The generated Dart class
       */
      function generateClass(cls) {
        const className = cls.name;
        const description = cls.description ? `/// ${cls.description}\n` : "";
        const properties = Object.values(cls.properties)
          .map(generateProperty)
          .join("\n");

        const constructorParams = Object.values(cls.properties)
          .map((prop) => `this.${prop.name}`)
          .join(", ");

        return `
${description}@JsonSerializable()
class ${className} {
${properties}
  ${className}({${constructorParams}});

  factory ${className}.fromJson(Map<String, dynamic> json) => _$${className}FromJson(json);

  Map<String, dynamic> toJson() => _$${className}ToJson(this);
}
`;
      }

      const imports = `import 'package:json_annotation/json_annotation.dart';

part '${StringUtils.camelToSnakeCase(classes[0].name)}.g.dart';
    
`;
      const generatedClasses = classes.map(generateClass).join("\n");
      return imports + generatedClasses;
    }

    /**
     * Generate kotlin classes
     * @param {Class[]} classes
     */
    static generateKotlinClasses(classes) {
      /**
       * @param {Property} prop
       * @returns {string} - 对应的dart类型
       */
      function convertToKotlinType(prop) {
        switch (prop.type) {
          case DataType.STRING:
            return "String?";
          case DataType.BOOLEAN:
            return "Boolean";
          case DataType.NUMBER:
            return "Double";
          case DataType.INTEGER:
            return "Int";
          case DataType.LONG:
            return "Long";
          case DataType.FLOAT:
            return "Double";
          case DataType.OBJECT:
            return StringUtils.capitalizeFirstLetter(prop.name) + "?";
          case DataType.ARRAY:
            if (prop.items) {
              const itemType = convertToKotlinType(prop.items);
              return `List<${itemType}>?`;
            } else {
              return `List<Any>?`;
            }
          default:
            return "Any?";
        }
      }

      /**
       * Generate Kotlin property
       * @param {Property} prop - The property
       * @returns {string} - The generated kotlin property
       */
      function generateProperty(prop) {
        let type = convertToKotlinType(prop);
        const description = prop.description
          ? `  /** ${prop.description} */\n`
          : "";
        return `${description}  @SerialName(name: "${prop.obfuscateName}")\n  val ${prop.name}: ${type},\n`;
      }

      /**
       * Generate Kotlin class
       * @param {Class} cls - The class
       * @returns {string} - The generated Kotlin class
       */
      function generateClass(cls) {
        const className = cls.name;
        const description = cls.description
          ? `/** ${cls.description} */\n`
          : "";
        const properties = Object.values(cls.properties)
          .map(generateProperty)
          .join("\n");

        return `
${description}@Serializable
class ${className}(
${properties}
)
`;
      }

      const imports = `import kotlinx.serialization.SerialName;
import kotlinx.serialization.Serializable;
`;
      const generatedClasses = classes.map(generateClass).join("\n");
      return imports + generatedClasses;
    }
  }

  /**
   * @param {string} code
   */
  function showCodePanel(code) {
    // Create code panel element
    let codePanel = document.createElement("div");
    codePanel.id = "codePanel";
    codePanel.style.position = "fixed";
    codePanel.style.top = "0";
    codePanel.style.left = "0";
    codePanel.style.width = "100%";
    codePanel.style.height = "100%";
    codePanel.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
    codePanel.style.border = "1px solid #ccc";
    codePanel.style.padding = "10px";
    codePanel.style.zIndex = "9998";

    let codePanelContent = document.createElement("div");
    codePanelContent.style.position = "absolute";
    codePanelContent.style.top = "50%";
    codePanelContent.style.left = "50%";
    codePanelContent.style.transform = "translate(-50%, -50%)";
    codePanelContent.style.width = "80%";
    codePanelContent.style.height = "80%";
    codePanelContent.style.backgroundColor = "#fff";
    codePanelContent.style.border = "1px solid #ccc";
    codePanelContent.style.padding = "10px";
    codePanelContent.style.overflow = "auto";
    codePanelContent.innerHTML = `<pre><code class="language-javascript">${code
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")}</code></pre>`;
    Prism.highlightElement(codePanelContent.querySelector("code"));
    codePanel.appendChild(codePanelContent);
    document.body.appendChild(codePanel);

    codePanel.addEventListener("click", function (event) {
      if (event.target === codePanel) {
        document.body.removeChild(codePanel);
      }
    });
  }

  /**
   * @param {string} apiId
   */
  async function getApiBodyData(apiId) {
    let url = "https://yapi.lioncash.co/api/interface/get?id=" + apiId;
    let response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    return await response.json();
  }

  /**
   * @param {string} apiId
   */
  function showButtons(apiId) {
    let oldButtons = document.querySelectorAll("h2.interface-title>button");
    for (const oldButton of oldButtons) {
      oldButton.parentNode.removeChild(oldButton);
    }

    let titles = document.querySelectorAll("h2.interface-title");
    for (const title of titles) {
      const isReq = title.textContent == "请求参数";
      const isRes = title.textContent == "返回数据";
      if (!isReq && !isRes) {
        continue;
      }
      const button = document.createElement("button");
      button.textContent = "Code";
      button.addEventListener("click", async () => {
        const data = await getApiBodyData(apiId);
        const schemaJson = isReq
          ? data.data.req_body_other
          : data.data.res_body;
        const schema = JSON.parse(schemaJson);
        const classes = SchemaParser.parse(schema);
        for (const cls of classes) {
          console.log(cls.name);
        }
        if (config.codeType == CodeType.DART) {
          showCodePanel(CodeGenerator.generateDartClasses(classes));
        } else if (config.codeType == CodeType.KOTLIN) {
          showCodePanel(CodeGenerator.generateKotlinClasses(classes));
        }
      });
      title.appendChild(button);
    }
  }

  function onRouterChanged() {
    let router = window.location.href;
    console.log("onRouteChanged", router);
    let matchResult = router.match(/.+\/project\/(\d+)\/interface\/api\/(\d+)/);
    if (matchResult) {
      // let projectId = matchResult[1];
      let apiId = matchResult[2];
      console.log("apiId", apiId);
      onElementReady("div.caseContainer", () => {
        console.log("Element Ready");
        showButtons(apiId);
      });
    }
  }

  function onElementReady(selector, callback) {
    if (document.querySelector(selector)) {
      callback();
    } else {
      const observer = new MutationObserver((mutations, obs) => {
        if (document.querySelector(selector)) {
          callback();
          obs.disconnect();
        }
      });

      observer.observe(document, {
        childList: true,
        subtree: true,
      });
    }
  }

  function loadScript(url, callback) {
    const script = document.createElement("script");
    script.type = "text/javascript";
    script.src = url;
    script.onload = callback;
    document.head.appendChild(script);
  }

  // Function to dynamically load a CSS file
  function loadCSS(url) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = url;
    document.head.appendChild(link);
  }

  window.onload = function () {
    loadScript(
      "https://cdnjs.cloudflare.com/ajax/libs/prism/9000.0.1/prism.min.js"
    );
    loadCSS(
      "https://cdnjs.cloudflare.com/ajax/libs/prism/9000.0.1/themes/prism.min.css"
    );
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

    window.addEventListener("popstate", onRouterChanged);
  };

  onRouterChanged();

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      let codePanel = document.getElementById("codePanel");
      if (codePanel) {
        event.preventDefault();
        document.body.removeChild(codePanel);
      }
    } else if (event.ctrlKey && event.key === "a") {
      let codePanel = document.getElementById("codePanel");
      if (codePanel) {
        event.preventDefault();
        const codeElement = codePanel.querySelector("code");
        let range = document.createRange();
        range.selectNodeContents(codeElement);
        let selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      }
    }
  });
})();
