export async function runReportsAndSimulationSmoke(page, baseUrl) {
  console.log("Opening reports route...");
  await page.goto(`${baseUrl}/reports?report=latest&tab=overview`, {
    waitUntil: "domcontentloaded",
  });
  await page.getByText("Dashboard-first report review").waitFor();
  await page.getByRole("link", { name: "Reports" }).waitFor();

  console.log("Opening simulation route...");
  await page.goto(`${baseUrl}/simulation?job=job-1&tab=live`, {
    waitUntil: "domcontentloaded",
  });
  await page.getByText("Live Event Stream").waitFor();
  await page.getByRole("link", { name: "Simulation" }).waitFor();
}
