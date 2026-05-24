import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function Profile() {
  const profileQuery = trpc.profile.get.useQuery();
  const updateProfileMutation = trpc.profile.update.useMutation();

  const [formData, setFormData] = useState({
    fullName: "",
    phone: "",
    addressStreet: "3765 Grosvenor Rd",
    addressCity: "South Euclid",
    addressState: "OH",
    addressZip: "44118",
    linkedIn: "",
    github: "",
    prefUsername: "khalawright5",
    prefPasswordHint: "JobWatch2026!",
    resumeA: "",
    resumeB: "",
    passionStatement: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProfileMutation.mutateAsync(formData);
  };

  if (profileQuery.isLoading) {
    return <div className="text-center py-8">Loading profile...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profile Settings</h1>
        <p className="text-muted-foreground mt-2">Manage your personal information and preferences</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Your basic contact details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="Your name"
                />
              </div>
              <div>
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="Your phone number"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address */}
        <Card>
          <CardHeader>
            <CardTitle>Address</CardTitle>
            <CardDescription>Your residential address for applications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="addressStreet">Street Address</Label>
              <Input
                id="addressStreet"
                name="addressStreet"
                value={formData.addressStreet}
                onChange={handleChange}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="addressCity">City</Label>
                <Input
                  id="addressCity"
                  name="addressCity"
                  value={formData.addressCity}
                  onChange={handleChange}
                />
              </div>
              <div>
                <Label htmlFor="addressState">State</Label>
                <Input
                  id="addressState"
                  name="addressState"
                  value={formData.addressState}
                  onChange={handleChange}
                  maxLength={2}
                />
              </div>
              <div>
                <Label htmlFor="addressZip">ZIP Code</Label>
                <Input
                  id="addressZip"
                  name="addressZip"
                  value={formData.addressZip}
                  onChange={handleChange}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Social & Web */}
        <Card>
          <CardHeader>
            <CardTitle>Social & Web</CardTitle>
            <CardDescription>Your online profiles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="linkedIn">LinkedIn URL</Label>
                <Input
                  id="linkedIn"
                  name="linkedIn"
                  value={formData.linkedIn}
                  onChange={handleChange}
                  placeholder="https://linkedin.com/in/..."
                />
              </div>
              <div>
                <Label htmlFor="github">GitHub URL</Label>
                <Input
                  id="github"
                  name="github"
                  value={formData.github}
                  onChange={handleChange}
                  placeholder="https://github.com/..."
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Login Helper */}
        <Card>
          <CardHeader>
            <CardTitle>Login Helper</CardTitle>
            <CardDescription>Preferred credentials for job portals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="prefUsername">Preferred Username</Label>
                <Input
                  id="prefUsername"
                  name="prefUsername"
                  value={formData.prefUsername}
                  onChange={handleChange}
                />
              </div>
              <div>
                <Label htmlFor="prefPasswordHint">Password Hint</Label>
                <Input
                  id="prefPasswordHint"
                  name="prefPasswordHint"
                  value={formData.prefPasswordHint}
                  onChange={handleChange}
                  placeholder="e.g., JobWatch2026!"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Resumes */}
        <Card>
          <CardHeader>
            <CardTitle>Resumes</CardTitle>
            <CardDescription>Your resume versions for different roles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="resumeA">Resume A (Security Focus)</Label>
              <Textarea
                id="resumeA"
                name="resumeA"
                value={formData.resumeA}
                onChange={handleChange}
                placeholder="Paste your security-focused resume here..."
                rows={6}
              />
            </div>
            <div>
              <Label htmlFor="resumeB">Resume B (Support Focus)</Label>
              <Textarea
                id="resumeB"
                name="resumeB"
                value={formData.resumeB}
                onChange={handleChange}
                placeholder="Paste your support-focused resume here..."
                rows={6}
              />
            </div>
          </CardContent>
        </Card>

        {/* Passion Statement */}
        <Card>
          <CardHeader>
            <CardTitle>Passion Statement</CardTitle>
            <CardDescription>Your professional summary</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              name="passionStatement"
              value={formData.passionStatement}
              onChange={handleChange}
              placeholder="Tell us about your professional goals and interests..."
              rows={4}
            />
          </CardContent>
        </Card>

        <Button type="submit" size="lg" disabled={updateProfileMutation.isPending}>
          {updateProfileMutation.isPending ? "Saving..." : "Save Profile"}
        </Button>
      </form>
    </div>
  );
}
