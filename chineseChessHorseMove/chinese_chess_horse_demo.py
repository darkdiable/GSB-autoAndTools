import pygame
import random
import sys

# 棋盘参数
BOARD_COLS = 9  # 9列
BOARD_ROWS = 10 # 10行
CELL_SIZE = 60  # 每个格子的大小
MARGIN = 50     # 边缘留白

# 颜色定义
COLOR_BOARD = (241, 217, 185)  # 棋盘颜色
COLOR_LINE = (0, 0, 0)           # 线条颜色
COLOR_HORSE = (255, 0, 0)        # 马的颜色
COLOR_HIGHLIGHT = (0, 255, 0)    # 高亮目标点颜色
COLOR_RIVER = (0, 100, 255)      # 楚河汉界颜色
COLOR_TEXT = (0, 0, 0)            # 文字颜色

# 动画参数
ANIMATION_DURATION = 0.3  # 动画时间（秒）
STAY_DURATION = 0.5       # 停留时间（秒）
FPS = 60                   # 帧率

class ChessBoard:
    """棋盘绘制类"""
    
    def __init__(self, screen):
        self.screen = screen
        self.width = MARGIN * 2 + CELL_SIZE * (BOARD_COLS - 1)
        self.height = MARGIN * 2 + CELL_SIZE * (BOARD_ROWS - 1)
    
    def get_board_position(self, col, row):
        """将棋盘坐标转换为屏幕坐标"""
        x = MARGIN + col * CELL_SIZE
        y = MARGIN + row * CELL_SIZE
        return (x, y)
    
    def draw(self):
        """绘制棋盘"""
        # 填充背景
        self.screen.fill(COLOR_BOARD)
        
        # 绘制竖线
        for col in range(BOARD_COLS):
            start_pos = self.get_board_position(col, 0)
            end_pos = self.get_board_position(col, BOARD_ROWS - 1)
            pygame.draw.line(self.screen, COLOR_LINE, start_pos, end_pos, 2)
        
        # 绘制横线（楚河汉界中间不画）
        for row in range(BOARD_ROWS):
            if row == 4 or row == 5:
                # 楚河汉界位置，只画两边
                start_pos_left = self.get_board_position(0, row)
                end_pos_left = self.get_board_position(0, row)
                pygame.draw.line(self.screen, COLOR_LINE, start_pos_left, end_pos_left, 2)
                
                start_pos_right = self.get_board_position(BOARD_COLS - 1, row)
                end_pos_right = self.get_board_position(BOARD_COLS - 1, row)
                pygame.draw.line(self.screen, COLOR_LINE, start_pos_right, end_pos_right, 2)
            else:
                start_pos = self.get_board_position(0, row)
                end_pos = self.get_board_position(BOARD_COLS - 1, row)
                pygame.draw.line(self.screen, COLOR_LINE, start_pos, end_pos, 2)
        
        # 绘制楚河汉界中间的文字
        river_rect = pygame.Rect(
            self.get_board_position(0, 4)[0] + CELL_SIZE,
            self.get_board_position(0, 4)[1] + CELL_SIZE // 4,
            CELL_SIZE * (BOARD_COLS - 2),
            CELL_SIZE // 2
        )
        pygame.draw.rect(self.screen, COLOR_BOARD, river_rect)
        
        # 绘制楚河汉界文字
        font = pygame.font.Font(None, 48)
        text_chu = font.render("楚 河", True, COLOR_RIVER)
        text_han = font.render("汉 界", True, COLOR_RIVER)
        
        chu_pos = (
            self.get_board_position(2, 4)[0] + CELL_SIZE // 2,
            self.get_board_position(0, 4)[1] + CELL_SIZE // 2
        )
        han_pos = (
            self.get_board_position(6, 4)[0] + CELL_SIZE // 2,
            self.get_board_position(0, 4)[1] + CELL_SIZE // 2
        )
        
        self.screen.blit(text_chu, (chu_pos[0] - text_chu.get_width() // 2, chu_pos[1] - text_chu.get_height() // 2))
        self.screen.blit(text_han, (han_pos[0] - text_han.get_width() // 2, han_pos[1] - text_han.get_height() // 2))

class HorseMoveCalculator:
    """马走法计算器类"""
    
    # 马的8种可能走法（日字）
    # 格式：(dx, dy, block_dx, block_dy)
    # 其中 (dx, dy) 是目标位置相对于当前位置的偏移
    # (block_dx, block_dy) 是蹩马腿位置的偏移
    MOVES = [
        (1, 2, 0, 1),   # 右上
        (2, 1, 1, 0),   # 右上前
        (2, -1, 1, 0),  # 右下前
        (1, -2, 0, -1), # 右下
        (-1, -2, 0, -1),# 左下
        (-2, -1, -1, 0),# 左下前
        (-2, 1, -1, 0), # 左上前
        (-1, 2, 0, 1),  # 左上
    ]
    
    @staticmethod
    def is_valid_position(col, row):
        """检查位置是否在棋盘范围内"""
        return 0 <= col < BOARD_COLS and 0 <= row < BOARD_ROWS
    
    @staticmethod
    def is_leg_blocked(current_col, current_row, block_dx, block_dy, pieces):
        """
        检查是否蹩马腿
        pieces: 棋盘上的棋子字典，格式 {(col, row): piece_type}
        在这个演示中，除了马本身，棋盘是空的，所以pieces通常只有马的位置
        """
        block_col = current_col + block_dx
        block_row = current_row + block_dy
        
        # 如果蹩马腿位置在棋盘上且有棋子，则蹩马腿
        if HorseMoveCalculator.is_valid_position(block_col, block_row):
            if (block_col, block_row) in pieces:
                return True
        return False
    
    @staticmethod
    def get_valid_moves(current_col, current_row, pieces):
        """
        获取所有合法的走法
        current_col, current_row: 当前位置
        pieces: 棋盘上的棋子字典
        返回: 合法目标位置列表 [(col, row), ...]
        """
        valid_moves = []
        
        for dx, dy, block_dx, block_dy in HorseMoveCalculator.MOVES:
            target_col = current_col + dx
            target_row = current_row + dy
            
            # 检查目标位置是否在棋盘范围内
            if not HorseMoveCalculator.is_valid_position(target_col, target_row):
                continue
            
            # 检查是否蹩马腿
            if HorseMoveCalculator.is_leg_blocked(current_col, current_row, block_dx, block_dy, pieces):
                continue
            
            # 检查目标位置是否有己方棋子（在这个演示中，棋盘除马外全空，所以不需要）
            # 这里简化处理，只要目标位置在棋盘内且不蹩马腿，就是合法走法
            
            valid_moves.append((target_col, target_row))
        
        return valid_moves

class AnimationController:
    """动画控制器类"""
    
    def __init__(self, screen, board):
        self.screen = screen
        self.board = board
        self.clock = pygame.time.Clock()
        self.horse_radius = 20
    
    def draw_horse(self, pos, color=COLOR_HORSE):
        """绘制马棋子"""
        pygame.draw.circle(self.screen, color, pos, self.horse_radius)
        pygame.draw.circle(self.screen, COLOR_LINE, pos, self.horse_radius, 2)
    
    def draw_highlight(self, pos):
        """绘制高亮目标点"""
        # 绘制一个闪烁的圆
        pygame.draw.circle(self.screen, COLOR_HIGHLIGHT, pos, self.horse_radius + 5, 3)
    
    def smooth_move(self, start_pos, end_pos, duration):
        """
        平滑移动动画
        start_pos: 起始位置 (x, y)
        end_pos: 目标位置 (x, y)
        duration: 动画持续时间（秒）
        """
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # 计算总帧数
        total_frames = int(duration * FPS)
        
        for frame in range(total_frames):
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            # 计算当前位置（使用线性插值）
            progress = frame / total_frames
            current_x = start_x + (end_x - start_x) * progress
            current_y = start_y + (end_y - start_y) * progress
            
            # 重新绘制
            self.board.draw()
            self.draw_horse((int(current_x), int(current_y)))
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # 确保最终位置准确
        self.board.draw()
        self.draw_horse(end_pos)
        pygame.display.flip()
    
    def wait(self, duration):
        """
        等待指定时间
        duration: 等待时间（秒）
        """
        wait_frames = int(duration * FPS)
        for _ in range(wait_frames):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.clock.tick(FPS)

class HorseDemo:
    """马走日演示主类"""
    
    def __init__(self):
        # 初始化pygame
        pygame.init()
        
        # 计算窗口大小
        self.board_width = MARGIN * 2 + CELL_SIZE * (BOARD_COLS - 1)
        self.board_height = MARGIN * 2 + CELL_SIZE * (BOARD_ROWS - 1)
        
        # 创建窗口
        self.screen = pygame.display.set_mode((self.board_width, self.board_height))
        pygame.display.set_caption("中国象棋马走日演示")
        
        # 初始化组件
        self.board = ChessBoard(self.screen)
        self.animation = AnimationController(self.screen, self.board)
        
        # 随机选择起点
        self.start_col = random.randint(0, BOARD_COLS - 1)
        self.start_row = random.randint(0, BOARD_ROWS - 1)
        
        # 棋盘上的棋子（只有马本身）
        self.pieces = {(self.start_col, self.start_row): 'horse'}
        
        # 计算合法走法
        self.valid_moves = HorseMoveCalculator.get_valid_moves(
            self.start_col, self.start_row, self.pieces
        )
        
        print(f"随机起点: ({self.start_col}, {self.start_row})")
        print(f"合法走法数量: {len(self.valid_moves)}")
        print(f"合法走法: {self.valid_moves}")
    
    def run(self):
        """运行演示"""
        # 绘制初始状态
        self.board.draw()
        start_pos = self.board.get_board_position(self.start_col, self.start_row)
        self.animation.draw_horse(start_pos)
        pygame.display.flip()
        
        # 显示起点信息
        font = pygame.font.Font(None, 36)
        info_text = f"起点: ({self.start_col}, {self.start_row}), 合法走法: {len(self.valid_moves)}种"
        text_surface = font.render(info_text, True, COLOR_TEXT)
        self.screen.blit(text_surface, (10, 10))
        pygame.display.flip()
        
        # 等待2秒让用户看清起点
        self.animation.wait(2)
        
        # 依次演示每个合法走法
        for i, (target_col, target_row) in enumerate(self.valid_moves):
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            # 获取位置
            start_pos = self.board.get_board_position(self.start_col, self.start_row)
            target_pos = self.board.get_board_position(target_col, target_row)
            
            # 绘制高亮目标点
            self.board.draw()
            self.animation.draw_horse(start_pos)
            self.animation.draw_highlight(target_pos)
            
            # 显示当前走法信息
            move_text = f"走法 {i+1}/{len(self.valid_moves)}: ({self.start_col},{self.start_row}) -> ({target_col},{target_row})"
            text_surface = font.render(move_text, True, COLOR_TEXT)
            self.screen.blit(text_surface, (10, 10))
            pygame.display.flip()
            
            # 等待片刻让用户看到高亮
            self.animation.wait(0.5)
            
            # 平滑移动到目标点
            self.animation.smooth_move(start_pos, target_pos, ANIMATION_DURATION)
            
            # 停留一段时间
            self.animation.wait(STAY_DURATION)
            
            # 平滑移回起点
            self.animation.smooth_move(target_pos, start_pos, ANIMATION_DURATION)
            
            # 短暂停留
            self.animation.wait(0.2)
        
        # 全部演示完成，显示完成信息
        self.board.draw()
        self.animation.draw_horse(start_pos)
        
        # 显示完成信息
        font_large = pygame.font.Font(None, 48)
        complete_text = "演示完成！点击关闭按钮退出"
        text_surface = font_large.render(complete_text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=(self.board_width // 2, self.board_height // 2))
        self.screen.blit(text_surface, text_rect)
        
        pygame.display.flip()
        
        # 等待用户关闭窗口
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.animation.clock.tick(FPS)

def main():
    """主函数"""
    demo = HorseDemo()
    demo.run()

if __name__ == "__main__":
    main()
