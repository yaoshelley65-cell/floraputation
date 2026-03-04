/**
 * Floraputation — Pro User Database
 * Maintained manually by the Floraputation team.
 * To add a new Pro user, append an entry to PRO_USERS.
 *
 * Format:
 *   { email: "user@company.com", password: "hashed_or_plain", name: "Display Name", company: "Company Name", since: "YYYY-MM" }
 *
 * NOTE: This is a client-side demo database for prototype purposes.
 * In production, authentication should be handled server-side.
 */

const PRO_USERS = [
  {
    email: "yaoshelley65@gmail.com",
    password: "florapro2026",
    name: "Shelley Yao",
    company: "Floraputation (Admin)",
    since: "2026-03",
    role: "admin"
  }
  // Add more Pro users below:
  // {
  //   email: "user@breeder.com",
  //   password: "their_password",
  //   name: "John Smith",
  //   company: "ABC Breeding BV",
  //   since: "2026-04",
  //   role: "pro"
  // }
];

/**
 * Authenticate a user against the Pro database.
 * Returns the user object if found, or null.
 */
function authenticateUser(email, password) {
  const normalised = (email || '').toLowerCase().trim();
  return PRO_USERS.find(u =>
    u.email.toLowerCase() === normalised && u.password === password
  ) || null;
}

/**
 * Check if an email belongs to a Pro user (for session restore).
 */
function isProEmail(email) {
  const normalised = (email || '').toLowerCase().trim();
  return PRO_USERS.some(u => u.email.toLowerCase() === normalised);
}
