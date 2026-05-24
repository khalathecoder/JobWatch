import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function Companies() {
  const companiesQuery = trpc.companies.list.useQuery();
  const pendingQuery = trpc.companies.getPending.useQuery();
  const approveMutation = trpc.companies.approve.useMutation();
  const rejectMutation = trpc.companies.reject.useMutation();

  const handleApprove = async (id: number) => {
    await approveMutation.mutateAsync({ id });
    pendingQuery.refetch();
  };

  const handleReject = async (id: number) => {
    await rejectMutation.mutateAsync({ id });
    pendingQuery.refetch();
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Companies</h1>
        <p className="text-muted-foreground mt-2">Manage tracked companies and new suggestions</p>
      </div>

      <Tabs defaultValue="tracked" className="w-full">
        <TabsList>
          <TabsTrigger value="tracked">Tracked ({companiesQuery.data?.length || 0})</TabsTrigger>
          <TabsTrigger value="pending">Pending ({pendingQuery.data?.length || 0})</TabsTrigger>
        </TabsList>

        {/* Tracked Companies */}
        <TabsContent value="tracked" className="space-y-4">
          {companiesQuery.isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading companies...</div>
          ) : companiesQuery.data?.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">No tracked companies yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {companiesQuery.data?.map((company: any) => (
                <Card key={company.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle>{company.name}</CardTitle>
                        {company.atsType && <Badge className="mt-2">{company.atsType}</Badge>}
                      </div>
                      {company.verified && <Badge variant="outline">Verified</Badge>}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {company.careersUrl && (
                      <p className="text-sm">
                        <a href={company.careersUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          View Careers Page
                        </a>
                      </p>
                    )}
                    {company.sampleRoles && (
                      <p className="text-sm text-muted-foreground">
                        <strong>Sample Roles:</strong> {company.sampleRoles}
                      </p>
                    )}
                    {company.hasLiveRoles && (
                      <Badge variant="secondary">Has Live Roles</Badge>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Pending Suggestions */}
        <TabsContent value="pending" className="space-y-4">
          {pendingQuery.isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading suggestions...</div>
          ) : pendingQuery.data?.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">No pending suggestions</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {pendingQuery.data?.map((suggestion: any) => (
                <Card key={suggestion.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle>{suggestion.name}</CardTitle>
                        {suggestion.industry && (
                          <p className="text-sm text-muted-foreground mt-1">{suggestion.industry}</p>
                        )}
                      </div>
                      {suggestion.verified && <Badge>Verified</Badge>}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {suggestion.atsType && (
                      <p className="text-sm">
                        <strong>ATS:</strong> {suggestion.atsType}
                      </p>
                    )}
                    {suggestion.careersUrl && (
                      <p className="text-sm">
                        <a href={suggestion.careersUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          View Careers Page
                        </a>
                      </p>
                    )}
                    {suggestion.sampleRoles && (
                      <p className="text-sm text-muted-foreground">
                        <strong>Sample Roles:</strong> {suggestion.sampleRoles}
                      </p>
                    )}
                    {suggestion.hasLiveRoles && (
                      <Badge variant="secondary" className="block w-fit">
                        Has Live Roles
                      </Badge>
                    )}
                    <div className="flex gap-2 pt-4">
                      <Button
                        size="sm"
                        onClick={() => handleApprove(suggestion.id)}
                        disabled={approveMutation.isPending}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleReject(suggestion.id)}
                        disabled={rejectMutation.isPending}
                      >
                        Reject
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
