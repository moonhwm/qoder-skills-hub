// mf_grab.cs —— 零安装抓帧器：Windows Media Foundation（mfplat/mfreadwrite）→ RGB32 → BMP
// 用法（由 PowerShell Add-Type 引入后）：MfGrab.Run(videoPath, secondsList, outDirPrefix)
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;

public static class MfGrab
{
    [DllImport("mfplat.dll", ExactSpelling = true)] static extern int MFStartup(int Version, int dwFlags);
    [DllImport("mfplat.dll", ExactSpelling = true)] static extern int MFShutdown();
    [DllImport("mfplat.dll", ExactSpelling = true)] static extern int MFCreateMediaType(out IMFMediaType ppMFType);
    [DllImport("mfreadwrite.dll", ExactSpelling = true, CharSet = CharSet.Unicode)]
    static extern int MFCreateSourceReaderFromURL(string pwszURL, IntPtr pAttributes, out IMFSourceReader ppSourceReader);
    [DllImport("mfplat.dll", ExactSpelling = true)] static extern int MFCreateAttributes(out IMFAttributes ppMFAttributes, int cInitialSize);
    static readonly Guid MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING = new Guid("fb394f3d-ccf1-42ee-bbb3-f9b845d5681d");

    const int MF_VERSION = 0x00020070;
    static readonly Guid MF_MT_MAJOR_TYPE = new Guid("48eba18e-f8c9-4687-bf11-0a74c9f96a8f");
    static readonly Guid MF_MT_SUBTYPE = new Guid("f7e34c9a-42e8-4714-b74b-cb29d72c35e5");
    static readonly Guid MFMediaType_Video = new Guid("73646976-0000-0010-8000-00AA00389B71");
    static readonly Guid MFVideoFormat_RGB32 = new Guid("00000016-0000-0010-8000-00AA00389B71");
    static readonly Guid MF_PD_DURATION = new Guid("6c990d13-be bb-4778-98 65-a8 d6 0a e7 1f 2f".Replace(" ", ""));

    [ComImport, Guid("2CD2D921-C447-44A7-A13C-4ADABFC247E3"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMFAttributes
    {
        int GetItem(ref Guid guidKey, IntPtr pValue);
        int GetItemType(ref Guid guidKey, out int pType);
        int CompareItem(ref Guid guidKey, IntPtr value, out bool pbResult);
        int Compare(IMFAttributes pTheirs, int MatchType, out bool pbResult);
        int GetUINT32(ref Guid guidKey, out int punValue);
        int GetUINT64(ref Guid guidKey, out long punValue);
        int GetDouble(ref Guid guidKey, out double pfValue);
        int GetGUID(ref Guid guidKey, out Guid pguidValue);
        int GetStringLength(ref Guid guidKey, out int pcchLength);
        int GetString(ref Guid guidKey, IntPtr pwszValue, int cchBufSize, out int pcchLength);
        int GetAllocatedString(ref Guid guidKey, out IntPtr ppwszValue, out int pcchLength);
        int GetBlobSize(ref Guid guidKey, out int pcbBlobSize);
        int GetBlob(ref Guid guidKey, IntPtr pBuf, int cbBufSize, out int pcbBlobSize);
        int GetAllocatedBlob(ref Guid guidKey, out IntPtr ppBuf, out int pcbSize);
        int GetUnknown(ref Guid guidKey, ref Guid riid, out IntPtr ppv);
        int SetItem(ref Guid guidKey, IntPtr value);
        int DeleteItem(ref Guid guidKey);
        int DeleteAllItems();
        int SetUINT32(ref Guid guidKey, int unValue);
        int SetUINT64(ref Guid guidKey, long unValue);
        int SetDouble(ref Guid guidKey, double fValue);
        int SetGUID(ref Guid guidKey, ref Guid guidValue);
        int SetString(ref Guid guidKey, string wszValue);
        int SetBlob(ref Guid guidKey, IntPtr pBuf, int cbBufSize);
        int SetUnknown(ref Guid guidKey, [MarshalAs(UnmanagedType.IUnknown)] object pUnknown);
        int LockStore();
        int UnlockStore();
        int GetCount(out int pcItems);
        int GetItemByIndex(int unIndex, out Guid pguidKey, IntPtr pValue);
        int CopyAllItems(IMFAttributes pDest);
    }

    [ComImport, Guid("44AE0FA8-EA31-4109-8D2E-4CAE4997C555"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMFMediaType : IMFAttributes { }

    [ComImport, Guid("70AE66F2-C809-4E4F-8915-BDCB406B7993"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMFSourceReader
    {
        int GetStreamSelection(int dwStreamIndex, out bool pfSelected);
        int SetStreamSelection(int dwStreamIndex, bool fSelected);
        int GetNativeMediaType(int dwStreamIndex, int dwMediaTypeIndex, out IMFMediaType ppMediaType);
        int GetCurrentMediaType(int dwStreamIndex, out IMFMediaType ppMediaType);
        int SetCurrentMediaType(int dwStreamIndex, IntPtr pdwReserved, IMFMediaType pMediaType);
        int SetCurrentPosition(ref Guid guidTimeFormat, IntPtr varPosition);
        int ReadSample(int dwStreamIndex, int dwControlFlags, out int pdwActualStreamIndex, out int pdwStreamFlags, out long pllTimestamp, out IMFSample ppSample);
        int Flush(int dwStreamIndex);
        int GetServiceForStream(int dwStreamIndex, ref Guid guidService, ref Guid riid, out IntPtr ppvObject);
        int GetPresentationAttribute(int dwStreamIndex, ref Guid guidAttribute, IntPtr pvarAttribute);
    }

    [ComImport, Guid("C40A00F2-B93A-4D80-AE8C-5A1C634F58E4"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMFSample
    {
        int GetItem(ref Guid guidKey, IntPtr pValue);
        int GetItemType(ref Guid guidKey, out int pType);
        int CompareItem(ref Guid guidKey, IntPtr value, out bool pbResult);
        int Compare(IMFAttributes pTheirs, int MatchType, out bool pbResult);
        int GetUINT32(ref Guid guidKey, out int punValue);
        int GetUINT64(ref Guid guidKey, out long punValue);
        int GetDouble(ref Guid guidKey, out double pfValue);
        int GetGUID(ref Guid guidKey, out Guid pguidValue);
        int GetStringLength(ref Guid guidKey, out int pcchLength);
        int GetString(ref Guid guidKey, IntPtr pwszValue, int cchBufSize, out int pcchLength);
        int GetAllocatedString(ref Guid guidKey, out IntPtr ppwszValue, out int pcchLength);
        int GetBlobSize(ref Guid guidKey, out int pcbBlobSize);
        int GetBlob(ref Guid guidKey, IntPtr pBuf, int cbBufSize, out int pcbBlobSize);
        int GetAllocatedBlob(ref Guid guidKey, out IntPtr ppBuf, out int pcbSize);
        int GetUnknown(ref Guid guidKey, ref Guid riid, out IntPtr ppv);
        int SetItem(ref Guid guidKey, IntPtr value);
        int DeleteItem(ref Guid guidKey);
        int DeleteAllItems();
        int SetUINT32(ref Guid guidKey, int unValue);
        int SetUINT64(ref Guid guidKey, long unValue);
        int SetDouble(ref Guid guidKey, double fValue);
        int SetGUID(ref Guid guidKey, ref Guid guidValue);
        int SetString(ref Guid guidKey, string wszValue);
        int SetBlob(ref Guid guidKey, IntPtr pBuf, int cbBufSize);
        int SetUnknown(ref Guid guidKey, [MarshalAs(UnmanagedType.IUnknown)] object pUnknown);
        int LockStore();
        int UnlockStore();
        int GetCount(out int pcItems);
        int GetItemByIndex(int unIndex, out Guid pguidKey, IntPtr pValue);
        int CopyAllItems(IMFAttributes pDest);
        int GetSampleFlags(out int pdwSampleFlags);
        int SetSampleFlags(int dwSampleFlags);
        int GetSampleTime(out long phnsSampleTime);
        int SetSampleTime(long hnsSampleTime);
        int GetSampleDuration(out long phnsSampleDuration);
        int SetSampleDuration(long hnsSampleDuration);
        int GetBufferCount(out int pdwBufferCount);
        int GetBufferByIndex(int dwIndex, out IMFMediaBuffer ppBuffer);
        int ConvertToContiguousBuffer(out IMFMediaBuffer ppBuffer);
        int AddBuffer(IMFMediaBuffer pBuffer);
        int RemoveBufferByIndex(int dwIndex);
        int RemoveAllBuffers();
        int GetTotalLength(out int pcbTotalLength);
        int CopyToBuffer(IMFMediaBuffer pBuffer);
    }

    [ComImport, Guid("045FA593-8799-42B8-BC8D-8968C6453507"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMFMediaBuffer
    {
        int Lock(out IntPtr ppbBuffer, out int pcbMaxLength, out int pcbCurrentLength);
        int Unlock();
        int GetCurrentLength(out int pcbCurrentLength);
        int SetCurrentLength(int cbCurrentLength);
        int GetMaxLength(out int pcbMaxLength);
    }

    [DllImport("mfplat.dll", ExactSpelling = true)] static extern int MFCreateMemoryBuffer(int cbMaxLength, out IMFMediaBuffer ppBuffer);

    /// <summary>抓取指定秒数的帧，输出为 BMP；返回结果描述列表</summary>
    public static List<string> Run(string videoPath, double[] seconds, string outPrefix)
    {
        var log = new List<string>();
        int hr = MFStartup(MF_VERSION, 0);
        if (hr != 0) { log.Add("MFStartup 失败 hr=0x" + hr.ToString("X8")); return log; }
        IMFSourceReader reader = null;
        try
        {
            IMFAttributes attrs; MFCreateAttributes(out attrs, 1); Guid gProc = MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING; attrs.SetUINT32(ref gProc, 1);
            hr = MFCreateSourceReaderFromURL(videoPath, Marshal.GetIUnknownForObject(attrs), out reader);
            if (hr != 0) { log.Add("MFCreateSourceReaderFromURL 失败 hr=0x" + hr.ToString("X8")); return log; }
            IMFMediaType mt;
            hr = MFCreateMediaType(out mt);
            Guid g1 = MF_MT_MAJOR_TYPE, g2 = MF_MT_SUBTYPE;
            Guid vVideo = MFMediaType_Video, vRgb = MFVideoFormat_RGB32;
            mt.SetGUID(ref g1, ref vVideo);
            mt.SetGUID(ref g2, ref vRgb);
            hr = reader.SetCurrentMediaType(unchecked((int)0xFFFFFFFC), IntPtr.Zero, mt);   // MF_SOURCE_READER_FIRST_VIDEO_STREAM
            if (hr != 0) { log.Add("SetCurrentMediaType(RGB32) 失败 hr=0x" + hr.ToString("X8")); return log; }
            IMFMediaType cur;
            reader.GetCurrentMediaType(unchecked((int)0xFFFFFFFC), out cur);
            Guid gk = MF_MT_FRAME_SIZE_GUID;
            long packed; cur.GetUINT64(ref gk, out packed);
            int w = (int)(packed >> 32), h = (int)(packed & 0xFFFFFFFF);
            log.Add(string.Format("当前媒体类型：{0}x{1} RGB32", w, h));
            foreach (double sec in seconds)
            {
                var pos = PropVariant.FromLong((long)(sec * 10000000));
                Guid tf = Guid.Empty;   // GUID_NULL = 100ns 单位
                hr = reader.SetCurrentPosition(ref tf, pos.Ptr);
                int idx, flags; long ts; IMFSample sample;
                hr = reader.ReadSample(unchecked((int)0xFFFFFFFC), 0, out idx, out flags, out ts, out sample);
                if (hr != 0 || sample == null) { log.Add(string.Format("t={0}s ReadSample 失败 hr=0x{1:X8}", sec, hr)); continue; }
                IMFMediaBuffer buf;
                sample.ConvertToContiguousBuffer(out buf);
                IntPtr p; int maxLen, curLen;
                buf.Lock(out p, out maxLen, out curLen);
                int stride = w * 4;
                byte[] rgb = new byte[w * h * 3];
                for (int y = 0; y < h; y++)
                {
                    IntPtr row = (IntPtr)(p.ToInt64() + (long)y * stride);
                    for (int x = 0; x < w; x++)
                    {
                        // BGRA in memory → RGB
                        byte b = Marshal.ReadByte(row, x * 4);
                        byte g = Marshal.ReadByte(row, x * 4 + 1);
                        byte r = Marshal.ReadByte(row, x * 4 + 2);
                        int o = (y * w + x) * 3;
                        rgb[o] = b; rgb[o + 1] = g; rgb[o + 2] = r;   // 存为 BGR 供 BMP
                    }
                }
                buf.Unlock();
                string outPath = outPrefix + "_t" + sec.ToString("0") + ".bmp";
                WriteBmp(outPath, rgb, w, h);
                log.Add(string.Format("★ t={0}s ⇒ {1}", sec, Path.GetFileName(outPath)));
            }
        }
        catch (Exception ex) { log.Add("异常：" + ex.Message); }
        finally { try { if (reader != null) Marshal.ReleaseComObject(reader); } catch { } MFShutdown(); }
        return log;
    }

    /// <summary>★顺序读帧（不 seek）：按 ReadSample 逐帧，每 keepEvery 帧存一张 BMP，文件名含真实时间戳（毫秒）
    /// 用途：取得"真连续帧"，以修"按时间 seek 落于关键帧"之局限（P1）</summary>
    public static List<string> RunSeq(string videoPath, string outPrefix, int keepEvery, int maxFrames)
    {
        var log = new List<string>();
        int hr = MFStartup(MF_VERSION, 0);
        if (hr != 0) { log.Add("MFStartup 失败 hr=0x" + hr.ToString("X8")); return log; }
        IMFSourceReader reader = null;
        try
        {
            IMFAttributes attrs; MFCreateAttributes(out attrs, 1);
            Guid gProc = MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING; attrs.SetUINT32(ref gProc, 1);
            hr = MFCreateSourceReaderFromURL(videoPath, Marshal.GetIUnknownForObject(attrs), out reader);
            if (hr != 0) { log.Add("MFCreateSourceReaderFromURL 失败 hr=0x" + hr.ToString("X8")); return log; }
            IMFMediaType mt; MFCreateMediaType(out mt);
            Guid g1 = MF_MT_MAJOR_TYPE, g2 = MF_MT_SUBTYPE;
            Guid vVideo = MFMediaType_Video, vRgb = MFVideoFormat_RGB32;
            mt.SetGUID(ref g1, ref vVideo); mt.SetGUID(ref g2, ref vRgb);
            hr = reader.SetCurrentMediaType(unchecked((int)0xFFFFFFFC), IntPtr.Zero, mt);
            if (hr != 0) { log.Add("SetCurrentMediaType(RGB32) 失败 hr=0x" + hr.ToString("X8")); return log; }
            IMFMediaType cur; reader.GetCurrentMediaType(unchecked((int)0xFFFFFFFC), out cur);
            Guid gk = MF_MT_FRAME_SIZE_GUID; long packed; cur.GetUINT64(ref gk, out packed);
            int w = (int)(packed >> 32), h = (int)(packed & 0xFFFFFFFF);
            log.Add(string.Format("顺序读帧：{0}x{1} RGB32 ｜ 每 {2} 帧存一张 ｜ 上限 {3} 张", w, h, keepEvery, maxFrames));
            int n = 0, saved = 0;
            while (saved < maxFrames)
            {
                int idx, flags; long ts; IMFSample sample;
                hr = reader.ReadSample(unchecked((int)0xFFFFFFFC), 0, out idx, out flags, out ts, out sample);
                if (hr != 0) { log.Add("ReadSample hr=0x" + hr.ToString("X8")); break; }
                if ((flags & 0x2) != 0) { log.Add("★ 读到流末（ENDOFSTREAM），共 " + n + " 帧"); break; }   // MF_SOURCE_READERF_ENDOFSTREAM
                if (sample == null) continue;
                n++;
                if (n % keepEvery != 0) continue;
                IMFMediaBuffer buf; sample.ConvertToContiguousBuffer(out buf);
                IntPtr p; int maxLen, curLen; buf.Lock(out p, out maxLen, out curLen);
                int stride = w * 4; byte[] rgb = new byte[w * h * 3];
                for (int y = 0; y < h; y++)
                {
                    IntPtr row = (IntPtr)(p.ToInt64() + (long)y * stride);
                    for (int x = 0; x < w; x++)
                    {
                        byte b = Marshal.ReadByte(row, x * 4);
                        byte g = Marshal.ReadByte(row, x * 4 + 1);
                        byte r = Marshal.ReadByte(row, x * 4 + 2);
                        int o = (y * w + x) * 3;
                        rgb[o] = b; rgb[o + 1] = g; rgb[o + 2] = r;
                    }
                }
                buf.Unlock();
                long ms = ts / 10000;
                string outPath = outPrefix + "_f" + n.ToString("D4") + "_" + ms.ToString() + "ms.bmp";
                WriteBmp(outPath, rgb, w, h);
                saved++;
                log.Add(string.Format("★ 帧 {0}（t={1}ms）⇒ {2}", n, ms, Path.GetFileName(outPath)));
            }
            log.Add(string.Format("顺序读帧完成：读入 {0} 帧，落盘 {1} 张", n, saved));
        }
        catch (Exception ex) { log.Add("异常：" + ex.Message); }
        finally { try { if (reader != null) Marshal.ReleaseComObject(reader); } catch { } MFShutdown(); }
        return log;
    }

    /// <summary>★全帧率统计（不落盘）：顺序读所有帧，逐行输出「F帧号,时间戳ms,平均亮度,与前帧之平均绝对差」</summary>
    public static List<string> RunStats(string videoPath)
    {
        var log = new List<string>();
        int hr = MFStartup(MF_VERSION, 0);
        if (hr != 0) { log.Add("MFStartup 失败 hr=0x" + hr.ToString("X8")); return log; }
        IMFSourceReader reader = null;
        try
        {
            IMFAttributes attrs; MFCreateAttributes(out attrs, 1);
            Guid gProc = MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING; attrs.SetUINT32(ref gProc, 1);
            hr = MFCreateSourceReaderFromURL(videoPath, Marshal.GetIUnknownForObject(attrs), out reader);
            if (hr != 0) { log.Add("MFCreateSourceReaderFromURL 失败 hr=0x" + hr.ToString("X8")); return log; }
            IMFMediaType mt; MFCreateMediaType(out mt);
            Guid g1 = MF_MT_MAJOR_TYPE, g2 = MF_MT_SUBTYPE;
            Guid vVideo = MFMediaType_Video, vRgb = MFVideoFormat_RGB32;
            mt.SetGUID(ref g1, ref vVideo); mt.SetGUID(ref g2, ref vRgb);
            hr = reader.SetCurrentMediaType(unchecked((int)0xFFFFFFFC), IntPtr.Zero, mt);
            if (hr != 0) { log.Add("SetCurrentMediaType(RGB32) 失败 hr=0x" + hr.ToString("X8")); return log; }
            IMFMediaType cur; reader.GetCurrentMediaType(unchecked((int)0xFFFFFFFC), out cur);
            Guid gk = MF_MT_FRAME_SIZE_GUID; long packed; cur.GetUINT64(ref gk, out packed);
            int w = (int)(packed >> 32), h = (int)(packed & 0xFFFFFFFF);
            int npix = w * h;
            byte[] prevLum = null;
            int n = 0;
            while (true)
            {
                int idx, flags; long ts; IMFSample sample;
                hr = reader.ReadSample(unchecked((int)0xFFFFFFFC), 0, out idx, out flags, out ts, out sample);
                if (hr != 0) break;
                if ((flags & 0x2) != 0) break;
                if (sample == null) continue;
                n++;
                IMFMediaBuffer buf; sample.ConvertToContiguousBuffer(out buf);
                IntPtr p; int maxLen, curLen; buf.Lock(out p, out maxLen, out curLen);
                int stride = w * 4;
                byte[] lum = new byte[npix];
                long sum = 0;
                for (int y = 0; y < h; y++)
                {
                    IntPtr row = (IntPtr)(p.ToInt64() + (long)y * stride);
                    for (int x = 0; x < w; x++)
                    {
                        byte b = Marshal.ReadByte(row, x * 4);
                        byte g = Marshal.ReadByte(row, x * 4 + 1);
                        byte r = Marshal.ReadByte(row, x * 4 + 2);
                        int L = (int)((r * 299 + g * 587 + b * 114) / 1000);
                        lum[y * w + x] = (byte)L; sum += L;
                    }
                }
                buf.Unlock();
                double mean = (double)sum / npix;
                double mad = -1;
                if (prevLum != null)
                {
                    long acc = 0;
                    for (int i = 0; i < npix; i++) acc += Math.Abs(lum[i] - prevLum[i]);
                    mad = (double)acc / npix;
                }
                log.Add(string.Format("F{0},{1},{2:0.0000},{3:0.0000}", n, ts / 10000, mean, mad));
                prevLum = lum;
            }
            log.Add("FRAMES=" + n);
        }
        catch (Exception ex) { log.Add("异常：" + ex.Message); }
        finally { try { if (reader != null) Marshal.ReleaseComObject(reader); } catch { } MFShutdown(); }
        return log;
    }

    static readonly Guid MF_MT_FRAME_SIZE_GUID = new Guid("1652c33d-d6b2-4012-b834-72030849a37d");

    static void WriteBmp(string path, byte[] bgr, int w, int h)
    {
        int rowSize = w * 3;
        int pad = (4 - rowSize % 4) % 4;
        int dataSize = (rowSize + pad) * h;
        int fileSize = 54 + dataSize;
        using (var fs = new FileStream(path, FileMode.Create, FileAccess.Write))
        using (var bw = new BinaryWriter(fs))
        {
            bw.Write((byte)'B'); bw.Write((byte)'M');
            bw.Write(fileSize); bw.Write(0); bw.Write(54);
            bw.Write(40); bw.Write(w); bw.Write(h);
            bw.Write((short)1); bw.Write((short)24); bw.Write(0);
            bw.Write(dataSize); bw.Write(2835); bw.Write(2835); bw.Write(0); bw.Write(0);
            for (int y = h - 1; y >= 0; y--)
            {
                bw.Write(bgr, y * rowSize, rowSize);
                for (int k = 0; k < pad; k++) bw.Write((byte)0);
            }
        }
    }
}

// 最小 PROPVARIANT（仅支持 VT_I8）
public sealed class PropVariant : IDisposable
{
    IntPtr _p;
    public IntPtr Ptr { get { return _p; } }
    PropVariant()
    {
        _p = Marshal.AllocCoTaskMem(24);
        for (int i = 0; i < 24; i++) Marshal.WriteByte(_p, i, 0);
        Marshal.WriteInt16(_p, 0, 20);   // VT_I8
    }
    public static PropVariant FromLong(long v)
    {
        var pv = new PropVariant();
        Marshal.WriteInt64(pv._p, 8, v);
        return pv;
    }
    public void Dispose() { if (_p != IntPtr.Zero) { Marshal.FreeCoTaskMem(_p); _p = IntPtr.Zero; } }
}
