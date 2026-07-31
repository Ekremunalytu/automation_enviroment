const allowed = new Set(["openHelp"]);
function dispatch(message) {
  return typeof message?.type === "string" && allowed.has(message.type);
}
module.exports.activate = () => dispatch({ type: "openHelp" });
