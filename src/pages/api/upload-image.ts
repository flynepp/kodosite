import type { APIRoute } from 'astro';
import { writeFile } from 'fs/promises';
import { join } from 'path';

export const POST: APIRoute = async ({ request }) => {
  try {
    const formData = await request.formData();
    const file = formData.get('wangeditor-uploaded-image') as File;

    if (!file) {
      return new Response(
        JSON.stringify({
          errno: 1,
          message: '未找到上传文件',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      return new Response(
        JSON.stringify({
          errno: 1,
          message: '只能上传图片文件',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // 验证文件大小（最大 5MB）
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      return new Response(
        JSON.stringify({
          errno: 1,
          message: '图片大小不能超过 5MB',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // 生成唯一文件名
    const timestamp = Date.now();
    const randomStr = Math.random().toString(36).substring(2, 8);
    const ext = file.name.split('.').pop() || 'jpg';
    const fileName = `${timestamp}-${randomStr}.${ext}`;

    // 保存文件到 public/images/uploads/
    const uploadDir = join(process.cwd(), 'public', 'images', 'uploads');
    const filePath = join(uploadDir, fileName);

    // 将文件转换为 Buffer 并保存
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    await writeFile(filePath, buffer);

    // 返回图片 URL
    const url = `/images/uploads/${fileName}`;

    return new Response(
      JSON.stringify({
        errno: 0,
        data: {
          url: url,
          alt: file.name,
          href: url,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('图片上传失败:', error);
    return new Response(
      JSON.stringify({
        errno: 1,
        message: error.message || '图片上传失败',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
