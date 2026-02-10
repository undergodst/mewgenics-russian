#!/usr/bin/env python3
"""
Mewgenics GPAK Tool

  python gpak_tool.py extract-text              Extract text files to text_output/
  python gpak_tool.py patch [override_dir]       Patch gpak with translated files (default: override/)
  python gpak_tool.py restore                    Restore original from backup
"""

import struct, os, sys, shutil, time

GPAK = 'resources.gpak'
TEXT_EXT = {'.gon', '.csv', '.txt', '.ini', '.data'}


def read_directory(path):
    entries = []
    with open(path, 'rb') as f:
        n = struct.unpack('<I', f.read(4))[0]
        for _ in range(n):
            nl = struct.unpack('<H', f.read(2))[0]
            name = f.read(nl).decode('utf-8', 'replace')
            size = struct.unpack('<I', f.read(4))[0]
            entries.append((name, size))
        data_start = f.tell()
    return entries, data_start


def stream_copy(src, dst, size):
    rem = size
    while rem > 0:
        buf = src.read(min(rem, 8*1024*1024))
        if not buf: break
        dst.write(buf)
        rem -= len(buf)


def cmd_extract_text():
    entries, data_start = read_directory(GPAK)
    out_dir = 'text_output'
    os.makedirs(out_dir, exist_ok=True)
    offset = data_start
    count = 0

    with open(GPAK, 'rb') as f:
        for name, size in entries:
            ext = os.path.splitext(name)[1].lower()
            if ext in TEXT_EXT:
                f.seek(offset)
                data = f.read(size)
                out_path = os.path.join(out_dir, name.replace('\\', '/'))
                os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
                with open(out_path, 'wb') as of:
                    of.write(data)
                print(f'  {name} ({size:,}b)')
                count += 1
            offset += size

    print(f'\nExtracted {count} text files to {out_dir}/')


def cmd_patch(override_dir='override'):
    if not os.path.isdir(override_dir):
        print(f"ERROR: '{override_dir}' not found. Run translate.py first.")
        return

    overrides = {}
    for root, _, files in os.walk(override_dir):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, override_dir).replace(os.sep, '/')
            overrides[rel] = full

    if not overrides:
        print("No files in override directory.")
        return

    # Backup
    bak = GPAK + '.bak'
    if not os.path.exists(bak):
        print(f"Backing up to {bak}...")
        shutil.copy2(GPAK, bak)
    source = bak

    entries, data_start = read_directory(source)

    matched = {}
    for i, (name, _) in enumerate(entries):
        if name in overrides:
            matched[i] = overrides.pop(name)
            print(f"  Replacing: {name}")

    if overrides:
        print(f"  WARNING: no match for: {', '.join(overrides.keys())}")
    if not matched:
        print("Nothing to patch.")
        return

    new_entries = []
    for i, (name, size) in enumerate(entries):
        if i in matched:
            new_entries.append((name, os.path.getsize(matched[i])))
        else:
            new_entries.append((name, size))

    tmp = GPAK + '.tmp'
    print(f"Rebuilding {GPAK}...")
    t0 = time.time()

    with open(tmp, 'wb') as out:
        out.write(struct.pack('<I', len(new_entries)))
        for name, size in new_entries:
            nb = name.encode('utf-8')
            out.write(struct.pack('<H', len(nb)))
            out.write(nb)
            out.write(struct.pack('<I', size))

        with open(source, 'rb') as src:
            offset = data_start
            for i, (name, orig_size) in enumerate(entries):
                if i in matched:
                    with open(matched[i], 'rb') as ov:
                        stream_copy(ov, out, new_entries[i][1])
                else:
                    src.seek(offset)
                    stream_copy(src, out, orig_size)
                offset += orig_size
                if (i+1) % 3000 == 0:
                    print(f"  {(i+1)/len(entries)*100:.0f}%...")

    os.replace(tmp, GPAK)
    print(f"Done in {time.time()-t0:.1f}s. Patched {len(matched)} file(s).")


def cmd_restore():
    bak = GPAK + '.bak'
    if not os.path.exists(bak):
        print("No backup found.")
        return
    shutil.copy2(bak, GPAK)
    print("Restored from backup.")


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'extract-text':
        cmd_extract_text()
    elif cmd == 'patch':
        cmd_patch(sys.argv[2] if len(sys.argv) > 2 else 'override')
    elif cmd == 'restore':
        cmd_restore()
    else:
        print(__doc__)
