/**
 * Settings Page
 * User preferences and configuration
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useUIStore } from '@/stores/uiStore';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';

export function Settings() {
  const { mode, setMode, theme, setTheme } = useUIStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your preferences and configuration
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* UI Mode */}
        <Card>
          <CardHeader>
            <CardTitle>Interface Mode</CardTitle>
            <CardDescription>
              Choose between simple and advanced interface
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <RadioGroup value={mode} onValueChange={(value) => setMode(value as 'simple' | 'advanced')}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="simple" id="simple" />
                <Label htmlFor="simple" className="cursor-pointer">
                  <div>
                    <p className="font-medium">Simple Mode</p>
                    <p className="text-sm text-muted-foreground">
                      Easy-to-use interface for quick tasks
                    </p>
                  </div>
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="advanced" id="advanced" />
                <Label htmlFor="advanced" className="cursor-pointer">
                  <div>
                    <p className="font-medium">Advanced Mode</p>
                    <p className="text-sm text-muted-foreground">
                      Full-featured interface with all options
                    </p>
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        {/* Theme */}
        <Card>
          <CardHeader>
            <CardTitle>Theme</CardTitle>
            <CardDescription>
              Choose your preferred color scheme
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <RadioGroup value={theme} onValueChange={(value) => setTheme(value as any)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="light" id="light" />
                <Label htmlFor="light" className="cursor-pointer">Light</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="dark" id="dark" />
                <Label htmlFor="dark" className="cursor-pointer">Dark</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="system" id="system" />
                <Label htmlFor="system" className="cursor-pointer">System</Label>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

