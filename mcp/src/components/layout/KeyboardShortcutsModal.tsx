/**
 * Keyboard Shortcuts Modal
 * Shows all available keyboard shortcuts
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { KEYBOARD_SHORTCUTS } from '@/hooks/useKeyboardShortcuts';
import { Keyboard } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  open: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsModal({ open, onClose }: KeyboardShortcutsModalProps) {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  
  const formatKey = (key: string) => {
    if (key === 'Cmd') return isMac ? '⌘' : 'Ctrl';
    if (key === 'ESC') return 'Esc';
    return key;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {KEYBOARD_SHORTCUTS.map((category) => (
            <div key={category.category}>
              <h3 className="mb-3 text-sm font-semibold text-muted-foreground">
                {category.category}
              </h3>
              <div className="space-y-2">
                {category.shortcuts.map((shortcut, idx) => (
                  <Card key={idx} className="border-none bg-muted/30">
                    <CardContent className="flex items-center justify-between p-3">
                      <span className="text-sm">{shortcut.description}</span>
                      <div className="flex gap-1">
                        {shortcut.keys.map((key, keyIdx) => (
                          <span key={keyIdx} className="flex items-center gap-1">
                            <Badge
                              variant="outline"
                              className="px-2 py-0.5 font-mono text-xs"
                            >
                              {formatKey(key)}
                            </Badge>
                            {keyIdx < shortcut.keys.length - 1 && (
                              <span className="text-xs text-muted-foreground">+</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-lg bg-primary/5 p-3 text-sm text-muted-foreground">
          <p>
            💡 Tip: Press <Badge variant="outline" className="mx-1 font-mono text-xs">?</Badge> 
            anytime to see these shortcuts
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

