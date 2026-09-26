// jd_crack.c — ZipCrypto(传统PKZIP加密) 六位数字密码爆破 + CRC 真值验证
// 用法: ./jd_crack <zip路径>
// 输出: 真密码（stdout 一行），找不到则无输出，退出码 1
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

static unsigned int CRCTAB[256];
static void init_crc_tab(void){
    for (unsigned int i = 0; i < 256; i++){
        unsigned int c = i;
        for (int k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320u ^ (c >> 1)) : (c >> 1);
        CRCTAB[i] = c;
    }
}
static inline unsigned int crc_upd(unsigned int crc, unsigned char b){
    return CRCTAB[(crc ^ b) & 0xFF] ^ (crc >> 8);
}

typedef struct { unsigned int k0, k1, k2; } Keys;
static inline void upd(Keys* k, unsigned char b){
    k->k0 = crc_upd(k->k0, b);
    k->k1 = (k->k1 + (k->k0 & 0xFF)) * 134775813u + 1u;
    k->k2 = crc_upd(k->k2, (unsigned char)(k->k1 >> 24));
}
static inline unsigned char decbyte(Keys* k){
    unsigned int t = k->k2 | 2u;
    return (unsigned char)(((unsigned long long)t * (t ^ 1u)) >> 8);
}
static void keys_init(Keys* k, const char* pw){
    k->k0 = 0x12345678u; k->k1 = 0x23456789u; k->k2 = 0x34567890u;
    for (const char* p = pw; *p; p++) upd(k, (unsigned char)*p);
}

int main(int argc, char** argv){
    if (argc < 2){ fprintf(stderr, "usage: %s file.zip\n", argv[0]); return 2; }
    init_crc_tab();
    FILE* f = fopen(argv[1], "rb");
    if (!f){ perror("open"); return 2; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char* buf = malloc(sz);
    if (fread(buf, 1, sz, f) != (size_t)sz){ perror("read"); return 2; }
    fclose(f);
    if (memcmp(buf, "PK\x03\x04", 4)){ fprintf(stderr, "not zip\n"); return 2; }

    unsigned short fn_len = buf[26] | (buf[27] << 8);
    unsigned short ex_len = buf[28] | (buf[29] << 8);
    unsigned int comp_size = buf[18] | (buf[19]<<8) | (buf[20]<<16) | ((unsigned)buf[21]<<24);
    unsigned int comp_method = buf[8] | (buf[9] << 8);
    unsigned short flags = buf[6] | (buf[7] << 8);
    unsigned int modtime = buf[10] | (buf[11] << 8);
    long data_off = 30 + fn_len + ex_len;
    const unsigned char* enc = buf + data_off;
    if (comp_size > (unsigned int)(sz - data_off)) comp_size = sz - data_off;

    // 从中央目录取 CRC（local header 可能为 0）
    unsigned int crc = buf[14] | (buf[15]<<8) | (buf[16]<<16) | ((unsigned)buf[17]<<24);
    for (long i = sz - 22; i >= 0; i--){
        if (!memcmp(buf + i, "PK\x01\x02", 4)){
            crc = buf[i+16] | (buf[i+17]<<8) | (buf[i+18]<<16) | ((unsigned)buf[i+19]<<24);
            break;
        }
    }
    unsigned char chk = (flags & 0x08) ? (unsigned char)((modtime >> 8) & 0xFF)
                                       : (unsigned char)((crc >> 24) & 0xFF);

    char pw[7]; pw[6] = 0;
    unsigned char* dec = malloc(comp_size);
    unsigned char* out = malloc(1 << 22);  // 解压输出上限 4MB
    for (int i = 0; i < 1000000; i++){
        snprintf(pw, 7, "%06d", i);
        Keys k; keys_init(&k, pw);
        // 12 字节加密头
        int fail = 0;
        for (int j = 0; j < 12; j++){
            unsigned char p = enc[j] ^ decbyte(&k);
            upd(&k, p);
            if (j == 11 && p != chk){ fail = 1; break; }
        }
        if (fail) continue;
        // 通过 1 字节校验 → 解密全文 + CRC 真值验证
        for (unsigned int j = 12; j < comp_size; j++){
            unsigned char p = enc[j] ^ decbyte(&k);
            upd(&k, p);
            dec[j - 12] = p;
        }
        unsigned int dlen = comp_size - 12;
        uLong outlen = 1 << 22;
        int zr = 0;
        if (comp_method == 8){
            z_stream zs; memset(&zs, 0, sizeof zs);
            if (inflateInit2(&zs, -15) != Z_OK) continue;
            zs.next_in = dec; zs.avail_in = dlen;
            zs.next_out = out; zs.avail_out = outlen;
            zr = inflate(&zs, Z_FINISH);
            outlen = zs.total_out;
            inflateEnd(&zs);
            if (zr != Z_STREAM_END && zr != Z_OK) continue;
        } else if (comp_method == 0){
            memcpy(out, dec, dlen); outlen = dlen;
        } else continue;
        if (crc32(crc32(0L, Z_NULL, 0), out, outlen) == crc){
            printf("%s\n", pw);
            free(dec); free(out); free(buf);
            return 0;
        }
    }
    free(dec); free(out); free(buf);
    return 1;
}
