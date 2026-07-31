function platformFeature(platform) {
  return platform === "darwin" ? "native-menu" : "portable-menu";
}
module.exports.activate = () => platformFeature(process.platform);
