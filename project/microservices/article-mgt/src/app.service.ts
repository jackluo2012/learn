import { HttpCode, Injectable } from '@nestjs/common';
import { PrismaService } from './prisma/prisma.service';
import { deleteArticleDto, saveArticleDto } from './dto/dto';

@Injectable()
export class AppService {
  constructor(private readonly prismaService: PrismaService) { }
  async saveArticle(data: saveArticleDto) {
    try {
      await this.prismaService.$queryRaw`INSERT INTO article (title, content) VALUES (${data.title}, ${data.content})`;
      const articles = await this.getAllArticles();
      return {
        HttpCode: 200,
        message: 'Article saved successfully',
        data: articles.data,
      }
    }catch (error) {
      console.log(error)
      return {
        HttpCode: 400,
        message: 'Error saving article',
        data: null
      }
    }
  }

  async getAllArticles() {
    try {
      const articles = await this.prismaService.$queryRaw`SELECT * FROM article`
      return {
        HttpCode: 200,
        message: 'Articles fetched successfully',
        data: articles,
      }
    } catch (error) {
      console.log(error)
      return {
        HttpCode: 500,
        message: 'Error fetching articles',
        data: null
      }
    }
  }
  async deleteArticle(data: deleteArticleDto) {
    try {
      const id: number = parseInt(data.id);
      await this.prismaService.$queryRaw`DELETE FROM article WHERE id = ${id}`
      
      const articles  = await this.getAllArticles();
      
      return {
        HttpCode: 200,
        message: 'Article deleted successfully',
        data: articles,
      }
    } catch (error) {
      console.log(error)
      return {
        HttpCode: 500,
        message: 'Error deleting article',
        data: null
      }
    }
  }

  getHello(): string {
    return 'Hello World!';
  }
}
