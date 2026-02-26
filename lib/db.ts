import { PrismaClient } from "@prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";

const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };
const url = process.env.DATABASE_URL || "file:./prisma/dev.db";
if (!globalForPrisma.prisma) {
  const adapter = new PrismaBetterSqlite3({ url });
  globalForPrisma.prisma = new PrismaClient({ adapter });
}
export const prisma = globalForPrisma.prisma;
