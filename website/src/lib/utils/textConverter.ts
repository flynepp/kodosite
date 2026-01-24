import { slug } from "github-slugger";
// 修复 marked 导入方式
import { marked } from "marked";

// 确保 marked 可用
const markedParser = marked || (() => {
  console.warn('marked is not available');
  return { parse: (s: string) => s, parseInline: (s: string) => s };
})();

// slugify
export const slugify = (content: string) => {
  return slug(content);
};

// markdownify
export const markdownify = (content: string, div?: boolean) => {
  if (!content) return "";
  try {
    return div ? markedParser.parse(content) : markedParser.parseInline(content);
  } catch (error) {
    console.error('Markdown parse error:', error);
    return content;
  }
};

// humanize
export const humanize = (content: string) => {
  return content
    .replace(/^[\s_]+|[\s_]+$/g, "")
    .replace(/[_\s]+/g, " ")
    .replace(/[-\s]+/g, " ")
    .replace(/^[a-z]/, function (m) {
      return m.toUpperCase();
    });
};

// titleify
export const titleify = (content: string) => {
  const humanized = humanize(content);
  return humanized
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

// plainify
export const plainify = (content: string) => {
  if (!content) return "";
  try {
    const parseMarkdown: any = markedParser.parse(content);
    const filterBrackets = parseMarkdown.replace(/<\/?[^>]+(>|$)/gm, "");
    const filterSpaces = filterBrackets.replace(/[\r\n]\s*[\r\n]/gm, "");
    const stripHTML = htmlEntityDecoder(filterSpaces);
    return stripHTML;
  } catch (error) {
    console.error('Plainify error:', error);
    return content;
  }
};

// strip entities for plainify
const htmlEntityDecoder = (htmlWithEntities: string) => {
  let entityList: { [key: string]: string } = {
    "&nbsp;": " ",
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
    "&quot;": '"',
    "&#39;": "'",
  };
  let htmlWithoutEntities: string = htmlWithEntities.replace(
    /(&amp;|&lt;|&gt;|&quot;|&#39;)/g,
    (entity: string): string => {
      return entityList[entity];
    },
  );
  return htmlWithoutEntities;
};
