#!/usr/bin/env python3
"""Boot an actual ARM64 kernel and test authenticated guest processes over SSH."""
import argparse,os,pathlib,socket,subprocess,tempfile,time,signal
p=argparse.ArgumentParser();p.add_argument('distribution',choices=['debian','ubuntu']);p.add_argument('directory');p.add_argument('--qemu',default='qemu-system-aarch64');a=p.parse_args()
directory=pathlib.Path(a.directory).resolve();name=a.distribution
with tempfile.TemporaryDirectory(prefix='binux-vm-test-') as temp:
 work=pathlib.Path(temp);bootstrap=work/'bootstrap';bootstrap.mkdir();home=work/'home';home.mkdir(mode=0o700);state=work/'state';state.mkdir(mode=0o700)
 key=work/'key';subprocess.run(['ssh-keygen','-q','-t','rsa','-b','3072','-m','PEM','-N','','-f',str(key)],check=True)
 (bootstrap/'authorized_keys').write_bytes(key.with_suffix('.pub').read_bytes());(bootstrap/'uid').write_text(str(os.getuid()));(bootstrap/'lang').write_text('en')
 # Snapshot: tests must not modify the released base disk.
 with socket.socket() as available:available.bind(('127.0.0.1',0));port=available.getsockname()[1]
 args=[a.qemu,'-machine','virt','-cpu','cortex-a72','-smp','2','-m','1024','-accel','tcg,thread=multi,split-wx=on','-nodefaults','-nographic','-serial','stdio','-kernel',str(directory/f'{name}-kernel'),'-initrd',str(directory/f'{name}-initrd'),'-append','root=/dev/vda rw console=ttyAMA0 net.ifnames=0','-drive',f'file={directory}/{name}-disk.qcow2,if=none,id=root,format=qcow2,snapshot=on','-device','virtio-blk-pci,drive=root','-netdev',f'user,id=net,hostfwd=tcp:127.0.0.1:{port}-:22','-device','virtio-net-pci,netdev=net']
 for tag,path,readonly in [('binux-bootstrap',bootstrap,True),('binux-home',home,False),('binux-state',state,False)]:
  args+=['-fsdev',f'local,id={tag},path={path},security_model=none'+(',readonly=on' if readonly else ''),'-device',f'virtio-9p-pci,fsdev={tag},mount_tag={tag}']
 log=directory/f'{name}-boot-test.log'
 with log.open('wb') as output:
  process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT)
  try:
   known=work/'known_hosts';end=time.monotonic()+300
   while time.monotonic()<end:
    if process.poll() is not None:raise RuntimeError(f'VM exited {process.returncode}; inspect {log}')
    text=log.read_text(errors='replace')
    line=next((x for x in text.splitlines() if 'BINUX_SSH_HOSTKEY ssh-ed25519 ' in x),None)
    if line:
     hostkey=' '.join(line.split('BINUX_SSH_HOSTKEY ',1)[1].split()[:2]);known.write_text(f'[127.0.0.1]:{port} {hostkey}\n')
     break
    time.sleep(1)
   else:raise RuntimeError(f'Guest boot timed out; inspect {log}')
   ssh=['ssh','-i',str(key),'-p',str(port),'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o',f'UserKnownHostsFile={known}','-o','ConnectTimeout=5','binux@127.0.0.1']
   for attempt in range(30):
    check=subprocess.run([*ssh,'true'],capture_output=True)
    if check.returncode==0:break
    time.sleep(1)
   else:raise RuntimeError('Guest SSH authentication failed: '+check.stderr.decode(errors='replace'))
   checks="set -eu; test $(id -u) -eq "+str(os.getuid())+"; uname -r; . /etc/os-release; test \"$ID\" = "+name+"; python3 -c 'print(\"한국어 Python process\")'; printf shared-home > /home/binux/vm-test.txt; sudo apt-get -o APT::Update::Error-Mode=any update; pkg --help; pkg install -y nodejs npm; node -e 'console.log(\"Node process\")'; binux-pip install flask fastapi; python3 -m venv /home/binux/test-project; /home/binux/.venv/bin/python -c 'import flask,fastapi;print(\"pip Python dependencies installed\")'; npm install --prefix /home/binux/test-js express"
   import shlex
   subprocess.run([*ssh,'/usr/local/bin/binux-entry /home/binux /bin/bash -ec '+shlex.quote(checks)],check=True,timeout=1200)
   assert (home/'vm-test.txt').read_text()=='shared-home'
   # A wrong client key must fail even though the correct device was bootstrapped.
   other=work/'other';subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(other)],check=True)
   wrong=ssh.copy();wrong[2]=str(other)
   assert subprocess.run([*wrong,'true'],capture_output=True).returncode!=0
   print(f'PASS {name}: actual kernel boot, matching UID shared home, pinned SSH host key, rejected unpaired client, Python, Node.js, signed apt update')
  finally:
   process.terminate()
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait()
