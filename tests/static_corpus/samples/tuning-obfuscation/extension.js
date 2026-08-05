// Inert marker function: declared but never invoked.
function decodeMarker(value) { return Buffer.from(value, "base64").toString(); }
function executeMarker(value) { return eval(value); }
module.exports.activate = () => [decodeMarker.name, executeMarker.name];
