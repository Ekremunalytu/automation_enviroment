export async function runReportsAndSimulationSmoke(page, baseUrl) {
  console.log("Opening reports route...");
  await page.goto(`${baseUrl}/reports?report=latest&tab=overview`, {
    waitUntil: "domcontentloaded",
  });
  await page.getByText("Security report").waitFor();
  await page.getByRole("tab", { name: "Overview" }).waitFor();
  await page.getByRole("tab", { name: "Event ledger" }).waitFor();
  await page.getByRole("tab", { name: "Audit" }).waitFor();
  await page.getByRole("button", { name: /^Reports/u }).waitFor();

  console.log("Opening simulation route...");
  await page.goto(`${baseUrl}/simulation?job=job-1&tab=live`, {
    waitUntil: "domcontentloaded",
  });
  await page.getByText("Live event ledger").waitFor();
  await page.getByRole("button", { name: /^Simulation/u }).waitFor();
}
