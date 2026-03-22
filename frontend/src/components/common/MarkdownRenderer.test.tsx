/**
 * @jest-environment jsdom
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MarkdownRenderer } from './MarkdownRenderer';

describe('MarkdownRenderer', () => {
  it('renders nothing for null content', () => {
    const { container } = render(<MarkdownRenderer content={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing for undefined content', () => {
    const { container } = render(<MarkdownRenderer content={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing for empty string', () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a heading', () => {
    render(<MarkdownRenderer content="# Hello World" />);
    expect(screen.getByRole('heading', { name: 'Hello World', level: 1 })).toBeTruthy();
  });

  it('renders bold text', () => {
    render(<MarkdownRenderer content="**bold text**" />);
    const bold = document.querySelector('strong');
    expect(bold).toBeTruthy();
    expect(bold?.textContent).toBe('bold text');
  });

  it('renders italic text', () => {
    render(<MarkdownRenderer content="*italic text*" />);
    const em = document.querySelector('em');
    expect(em).toBeTruthy();
    expect(em?.textContent).toBe('italic text');
  });

  it('renders a link with target=_blank and rel=noopener noreferrer', () => {
    render(<MarkdownRenderer content="[visit](https://example.com)" />);
    const link = screen.getByRole('link', { name: 'visit' });
    expect(link).toBeTruthy();
    expect(link.getAttribute('href')).toBe('https://example.com');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
  });

  it('renders an image with alt text', () => {
    render(<MarkdownRenderer content="![alt text](https://example.com/image.png)" />);
    const img = screen.getByRole('img');
    expect(img).toBeTruthy();
    expect(img.getAttribute('src')).toBe('https://example.com/image.png');
    expect(img.getAttribute('alt')).toBe('alt text');
  });

  it('renders a code block with a language class', () => {
    render(<MarkdownRenderer content={'```python\nprint("hello")\n```'} />);
    // SyntaxHighlighter wraps in a div; verify code is present
    expect(document.body.textContent).toContain('print("hello")');
  });

  it('renders TypeScript code block with syntax highlighting', () => {
    render(<MarkdownRenderer content={'```typescript\nconst x: number = 1;\n```'} />);
    expect(document.body.textContent).toContain('const x: number = 1;');
  });

  it('renders Rust code block with syntax highlighting', () => {
    render(<MarkdownRenderer content={'```rust\nfn main() { println!("hello"); }\n```'} />);
    expect(document.body.textContent).toContain('fn main()');
  });

  it('renders Solidity code block with syntax highlighting', () => {
    render(<MarkdownRenderer content={'```solidity\ncontract Hello { }\n```'} />);
    expect(document.body.textContent).toContain('contract Hello');
  });

  it('renders inline code', () => {
    render(<MarkdownRenderer content="Use `npm install` to set up." />);
    const code = document.querySelector('code');
    expect(code).toBeTruthy();
    expect(code?.textContent).toBe('npm install');
  });

  it('renders an unordered list', () => {
    render(
      <MarkdownRenderer
        content={`- item one
- item two`}
      />,
    );
    const items = screen.getAllByRole('listitem');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toBe('item one');
    expect(items[1].textContent).toBe('item two');
  });

  it('renders an ordered list', () => {
    render(
      <MarkdownRenderer
        content={`1. first
2. second`}
      />,
    );
    expect(screen.getAllByRole('listitem').length).toBe(2);
  });

  it('renders a blockquote', () => {
    render(<MarkdownRenderer content="> quoted text" />);
    const bq = document.querySelector('blockquote');
    expect(bq).toBeTruthy();
    expect(bq?.textContent?.trim()).toBe('quoted text');
  });

  // GFM Table support
  it('renders GFM pipe markdown as an HTML table', () => {
    const md = '| A | B |\n|---|---|\n| 1 | 2 |';
    const { container } = render(<MarkdownRenderer content={md} />);
    expect(container.querySelector('table')).toBeTruthy();
    expect(container.querySelector('thead')).toBeTruthy();
    expect(container.querySelector('tbody')).toBeTruthy();
  });

  // GFM Task list support
  it('renders GFM task list with checkboxes', () => {
    const md = `- [x] completed task
- [ ] incomplete task`;
    const { container } = render(<MarkdownRenderer content={md} />);
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    expect(checkboxes.length).toBe(2);
    expect(checkboxes[0].hasAttribute('checked')).toBe(true);
    expect(checkboxes[1].hasAttribute('checked')).toBe(false);
    // Checkboxes should be disabled/readonly
    expect(checkboxes[0].hasAttribute('disabled') || checkboxes[0].hasAttribute('readonly')).toBe(true);
  });

  // GFM Strikethrough support
  it('renders GFM strikethrough', () => {
    render(<MarkdownRenderer content="~~strikethrough text~~" />);
    const del = document.querySelector('del');
    expect(del).toBeTruthy();
    expect(del?.textContent).toBe('strikethrough text');
  });

  // GFM Autolink support
  it('renders GFM autolink (URL without markdown syntax)', () => {
    render(<MarkdownRenderer content="Visit https://example.com for more info" />);
    const link = screen.getByRole('link', { name: 'https://example.com' });
    expect(link).toBeTruthy();
    expect(link.getAttribute('href')).toBe('https://example.com');
    expect(link.getAttribute('target')).toBe('_blank');
  });

  it('applies custom className to wrapper', () => {
    const { container } = render(<MarkdownRenderer content="hello" className="custom-class" />);
    expect(container.firstChild).toBeTruthy();
    expect((container.firstChild as HTMLElement).className).toContain('custom-class');
  });

  // XSS protection - ensure no script execution
  it('does not render script tags (XSS protection)', () => {
    const { container } = render(
      <MarkdownRenderer content={'<script>alert("xss")</script>'} />
    );
    // Script tags should not be rendered as actual script elements
    expect(container.querySelector('script')).toBeNull();
    // The content should be escaped/encoded, not executed
    // react-markdown escapes raw HTML, so the script content appears as text
    expect(container.textContent).toContain('<script>');
    expect(container.textContent).toContain('</script>');
  });

  // XSS protection - ensure no event handlers
  it('does not render onclick handlers (XSS protection)', () => {
    const { container } = render(
      <MarkdownRenderer content={'<a onclick="alert(1)">click</a>'} />
    );
    const link = container.querySelector('a');
    expect(link).toBeNull(); // Raw HTML should not be rendered
  });
});