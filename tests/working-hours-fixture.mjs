
// web/copy-values.js (значок «скопировать» у значений) для наборов, что исполняют main.js в vm без импортов.
export async function loadCopyValues(hub={lang:'en'}) {
  const id=++instance;
  const textURL=moduleURL(readFileSync(new URL('../web/ui-text.js',import.meta.url),'utf8'),id);
  const {bindHub}=await import(textURL);bindHub(hub);
  const source=readFileSync(new URL('../web/copy-values.js',import.meta.url),'utf8')
    .replace(/from ["']\.\/ui-text\.js["']/g,'from '+JSON.stringify(textURL));
  const {decorateValues,valueElement}=await import(moduleURL(source,id));
  return {decorateValues,valueElement};
}
