import { z } from "zod";

const schema = z.object({
  API_BASE_URL: z.string().url().optional().default("http://localhost:8000"),
});

const data = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
};

export const environment = schema.parse(data);
