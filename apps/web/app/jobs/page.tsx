import JobsPageClient from "./jobs-page-client";

type JobsPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function JobsPage({ searchParams }: JobsPageProps) {
  const initialSearchParams = searchParams ? await searchParams : undefined;

  return <JobsPageClient initialSearchParams={initialSearchParams} />;
}
