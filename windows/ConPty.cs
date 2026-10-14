using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace Binux;

/// <summary>Real Windows pseudo console. Child tree belongs to a kill-on-close Job.</summary>
public sealed class ConPty : IDisposable
{
    private IntPtr pseudoConsole, process, job;
    private FileStream? input, output;
    private int disposed;
    public event Action<byte[]>? Output;
    public event Action<int>? Exited;
    public uint Pid { get; private set; }

    public void Start(string command, string directory, short cols=100, short rows=30)
    {
        if (pseudoConsole != IntPtr.Zero) throw new InvalidOperationException("Session already started");
        IntPtr inRead=IntPtr.Zero, inWrite=IntPtr.Zero, outRead=IntPtr.Zero, outWrite=IntPtr.Zero;
        IntPtr attributes=IntPtr.Zero;
        try
        {
            Check(CreatePipe(out inRead,out inWrite,IntPtr.Zero,0));
            Check(CreatePipe(out outRead,out outWrite,IntPtr.Zero,0));
            Marshal.ThrowExceptionForHR(CreatePseudoConsole(new Coord(cols,rows),inRead,outWrite,0,out pseudoConsole));
            CloseHandle(inRead); inRead=IntPtr.Zero;
            CloseHandle(outWrite); outWrite=IntPtr.Zero;
            UIntPtr size=UIntPtr.Zero;
            InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref size);
            attributes=Marshal.AllocHGlobal(checked((int)size.ToUInt64()));
            Check(InitializeProcThreadAttributeList(attributes,1,0,ref size));
            Check(UpdateProcThreadAttribute(attributes,0,(IntPtr)0x00020016,pseudoConsole,(UIntPtr)IntPtr.Size,IntPtr.Zero,IntPtr.Zero));
            var startup=new StartupInfoEx { Info=new StartupInfo { Cb=Marshal.SizeOf<StartupInfoEx>() }, Attributes=attributes };
            Check(CreateProcess(null,new StringBuilder(command),IntPtr.Zero,IntPtr.Zero,false,0x00080000|0x00000400|0x00000004,IntPtr.Zero,directory,ref startup,out var info));
            process=info.Process; Pid=info.ProcessId;
            job=CreateJobObject(IntPtr.Zero,null);
            if(job==IntPtr.Zero) { TerminateProcess(process,1); CloseHandle(info.Thread); throw new Win32Exception(); }
            var limits=new JobExtendedLimits { Basic=new JobBasicLimits { LimitFlags=0x00002000 } };
            IntPtr buffer=Marshal.AllocHGlobal(Marshal.SizeOf<JobExtendedLimits>());
            try
            {
                Marshal.StructureToPtr(limits,buffer,false);
                if(!SetInformationJobObject(job,9,buffer,(uint)Marshal.SizeOf<JobExtendedLimits>()) || !AssignProcessToJobObject(job,process))
                {
                    TerminateProcess(process,1); CloseHandle(info.Thread);
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
            }
            finally { Marshal.FreeHGlobal(buffer); }
            input=new FileStream(new SafeFileHandle(inWrite,true),FileAccess.Write,4096,false); inWrite=IntPtr.Zero;
            output=new FileStream(new SafeFileHandle(outRead,true),FileAccess.Read,4096,false); outRead=IntPtr.Zero;
            ResumeThread(info.Thread); CloseHandle(info.Thread);
            _=Task.Run(() =>
            {
                try { byte[] bytes=new byte[8192]; int count; while((count=output.Read(bytes,0,bytes.Length))>0) Output?.Invoke(bytes[..count]); }
                catch(IOException) {} catch(ObjectDisposedException) {}
            });
            _=Task.Run(() => { WaitForSingleObject(process,0xFFFFFFFF); if(GetExitCodeProcess(process,out uint code)) Exited?.Invoke(unchecked((int)code)); });
        }
        catch { Dispose(); throw; }
        finally
        {
            if(attributes!=IntPtr.Zero) { DeleteProcThreadAttributeList(attributes); Marshal.FreeHGlobal(attributes); }
            foreach(var handle in new[]{inRead,inWrite,outRead,outWrite}) if(handle!=IntPtr.Zero) CloseHandle(handle);
        }
    }
    public void Write(string text)
    {
        if(input is null || Volatile.Read(ref disposed)!=0)return;
        try { byte[] data=Encoding.UTF8.GetBytes(text); lock(input) { input.Write(data); input.Flush(); } }
        catch(IOException) {} catch(ObjectDisposedException) {}
    }
    public void Resize(short cols,short rows) { if(pseudoConsole!=IntPtr.Zero && cols>0 && rows>0) Marshal.ThrowExceptionForHR(ResizePseudoConsole(pseudoConsole,new Coord(cols,rows))); }
    public void Dispose()
    {
        if(Interlocked.Exchange(ref disposed,1)!=0)return;
        input?.Dispose();
        if(job!=IntPtr.Zero) { TerminateJobObject(job,0); CloseHandle(job); job=IntPtr.Zero; }
        if(pseudoConsole!=IntPtr.Zero) { ClosePseudoConsole(pseudoConsole); pseudoConsole=IntPtr.Zero; }
        output?.Dispose();
        if(process!=IntPtr.Zero) { WaitForSingleObject(process,2000); CloseHandle(process); process=IntPtr.Zero; }
    }
    private static void Check(bool ok) { if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error()); }

    [StructLayout(LayoutKind.Sequential)] private readonly struct Coord(short x,short y) { public readonly short X=x,Y=y; }
    [StructLayout(LayoutKind.Sequential)] private struct StartupInfo { public int Cb; public IntPtr Reserved,Desktop,Title; public uint X,Y,XSize,YSize,XCountChars,YCountChars,FillAttribute,Flags; public ushort ShowWindow,ReservedBytes; public IntPtr ReservedData,StdInput,StdOutput,StdError; }
    [StructLayout(LayoutKind.Sequential)] private struct StartupInfoEx { public StartupInfo Info; public IntPtr Attributes; }
    [StructLayout(LayoutKind.Sequential)] private struct ProcessInfo { public IntPtr Process,Thread; public uint ProcessId,ThreadId; }
    [StructLayout(LayoutKind.Sequential)] private struct JobBasicLimits { public long PerProcessTime,PerJobTime; public uint LimitFlags; public UIntPtr MinWorkingSet,MaxWorkingSet; public uint ActiveProcessLimit; public UIntPtr Affinity; public uint Priority,Scheduling; }
    [StructLayout(LayoutKind.Sequential)] private struct IoCounters { public ulong ReadOperations,WriteOperations,OtherOperations,ReadBytes,WriteBytes,OtherBytes; }
    [StructLayout(LayoutKind.Sequential)] private struct JobExtendedLimits { public JobBasicLimits Basic; public IoCounters Io; public UIntPtr ProcessMemory,JobMemory,PeakProcessMemory,PeakJobMemory; }

    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool CreatePipe(out IntPtr read,out IntPtr write,IntPtr attributes,uint size);
    [DllImport("kernel32.dll")] private static extern int CreatePseudoConsole(Coord size,IntPtr input,IntPtr output,uint flags,out IntPtr console);
    [DllImport("kernel32.dll")] private static extern int ResizePseudoConsole(IntPtr console,Coord size);
    [DllImport("kernel32.dll")] private static extern void ClosePseudoConsole(IntPtr console);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,uint flags,ref UIntPtr size);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr attribute,IntPtr value,UIntPtr size,IntPtr previous,IntPtr returned);
    [DllImport("kernel32.dll")] private static extern void DeleteProcThreadAttributeList(IntPtr list);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] private static extern bool CreateProcess(string? app,StringBuilder command,IntPtr processAttributes,IntPtr threadAttributes,bool inherit,uint flags,IntPtr environment,string cwd,ref StartupInfoEx startup,out ProcessInfo process);
    [DllImport("kernel32.dll")] private static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll")] private static extern uint WaitForSingleObject(IntPtr handle,uint timeout);
    [DllImport("kernel32.dll")] private static extern bool GetExitCodeProcess(IntPtr process,out uint code);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] private static extern bool TerminateProcess(IntPtr process,uint code);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] private static extern IntPtr CreateJobObject(IntPtr attributes,string? name);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool SetInformationJobObject(IntPtr job,int infoClass,IntPtr info,uint length);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
    [DllImport("kernel32.dll")] private static extern bool TerminateJobObject(IntPtr job,uint code);
}
