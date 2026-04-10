import { redirect } from "next/navigation";

/** Root page — redirect to login */
export default function HomePage() {
  redirect("/login");
}
