import { HttpCode, Injectable } from '@nestjs/common';
import { PrismaService } from './prisma/prisma.service';
import { saveReaderDto } from './dto/dto';

@Injectable()
export class AppService {
  constructor(private readonly prismaService: PrismaService) { }

  async saveReader(data: saveReaderDto): Promise<any> {
    try {
      console.log(data);
      await this.prismaService.$queryRaw`INSERT INTO reader (email) VALUES (${data.email})`;
      const readers = await this.getAllReaders();
      return {
        HttpCode: 200,
        message: 'Reader saved successfully',
        // data: readers.data,
      }
    } catch (error) {
      return {
        HttpCode: 500,
        message: 'Error saving reader',
        data: null,
        error: error
      }
    }

  }
  async getAllReaders() {
    try {
      const readers = await this.prismaService.$queryRaw`SELECT * FROM reader`;
      return {
        HttpCode: 200,
        message: 'Readers retrieved successfully',
        data: readers,
      };
    } catch (error) {
      return {
        HttpCode: 500,
        message: 'Error retrieving readers',
        data: null,
      }

    }
  }
  getHello(): string {
    return 'Hello World!';
  }
}
