#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include "lib/bitvector.h"
#include "lib/boards.h"
#include "lib/bdict.h"
#include "lib/queue.h"
#include "lib/solution.h"
#include "lib/contracts.h"
#include "lib/xalloc.h"

typedef struct bfs_node {
   bitvector board;
   index_t move_row;
   index_t move_col;
   struct bfs_node* parent;
} bfs_node;

solution build_solution_from_path(bfs_node* solution_node, index_t width);

static void flip_and_replace(bitvector* board, index_t i) {
   bitvector temp = bitvector_flip(*board, i);
   bitvector_free(*board);
   *board = temp;
}

board_t make_move(board_t B, index_t row, index_t col) {
   REQUIRES(row < B.height);
   REQUIRES(col < B.width);
   
   bitvector new_board = bitvector_copy(B.data);
   
   index_t pressed_idx = row * B.width + col;
   flip_and_replace(&new_board, pressed_idx);
   
   if (row > 0) {
       index_t up_idx = (row - 1) * B.width + col;
       flip_and_replace(&new_board, up_idx);
   }
   
   if (row < B.height - 1) {
       index_t down_idx = (row + 1) * B.width + col;
       flip_and_replace(&new_board, down_idx);
   }
   
   if (col > 0) {
       index_t left_idx = row * B.width + (col - 1);
       flip_and_replace(&new_board, left_idx);
   }
   
   if (col < B.width - 1) {
       index_t right_idx = row * B.width + (col + 1);
       flip_and_replace(&new_board, right_idx);
   }
   
   board_t result = B;
   result.data = new_board;
   return result;
}

bool solved(board_t B) {
   for (index_t i = 0; i < B.width * B.height; i++) {
       if (bitvector_get(B.data, i)) {
           return false;
       }
   }
   return true;
}

solution solve(board_t B) {
   if (solved(B)) {
       return new_solution();
   }
   
   hdict_t visited = bdict_new(4096);
   queue_t Q = queue_new();
   queue_t all_nodes = queue_new();
   
   bfs_node* initial_node = xmalloc(sizeof(bfs_node));
   initial_node->board = bitvector_copy(B.data);
   initial_node->move_row = 0;
   initial_node->move_col = 0;
   initial_node->parent = NULL;
   
   board_data* initial_data = xmalloc(sizeof(board_data));
   initial_data->board = bitvector_copy(B.data);
   initial_data->move = 0;
   
   bdict_insert(visited, initial_data);
   enq(Q, initial_node);
   enq(all_nodes, initial_node);
   
   bfs_node* solution_node = NULL;
   
   while (!queue_empty(Q)) {
       bfs_node* current_node = (bfs_node*)deq(Q);
       
       board_t current_board = B;
       current_board.data = bitvector_copy(current_node->board);
       
       for (index_t row = 0; row < B.height && solution_node == NULL; row++) {
           for (index_t col = 0; col < B.width && solution_node == NULL; col++) {
               board_t new_board = make_move(current_board, row, col);
               
               if (bdict_lookup(visited, new_board.data) == NULL) {
                   bfs_node* new_node = xmalloc(sizeof(bfs_node));
                   new_node->board = bitvector_copy(new_board.data);
                   new_node->move_row = row;
                   new_node->move_col = col;
                   new_node->parent = current_node;
                   
                   board_data* new_data = xmalloc(sizeof(board_data));
                   new_data->board = bitvector_copy(new_board.data);
                   new_data->move = row * B.width + col;
                   
                   bdict_insert(visited, new_data);
                   enq(all_nodes, new_node);
                   
                   if (solved(new_board)) {
                       solution_node = new_node;
                   } else {
                       enq(Q, new_node);
                   }
               }
               
               bitvector_free(new_board.data);
           }
       }
       
       bitvector_free(current_board.data);
   }
   
   solution result = NULL;
   if (solution_node != NULL) {
       result = build_solution_from_path(solution_node, B.width);
   }
   
   queue_free(Q, NULL);
   
   while (!queue_empty(all_nodes)) {
       bfs_node* node = (bfs_node*)deq(all_nodes);
       bitvector_free(node->board);
       free(node);
   }
   queue_free(all_nodes, NULL);
   
   hdict_free(visited);
   
   return result;
}

solution build_solution_from_path(bfs_node* solution_node, index_t width) {
   REQUIRES(solution_node != NULL);
   
   solution S = new_solution();
   solution moves_reversed = new_solution();
   
   bfs_node* current = solution_node;
   
   while (current != NULL && current->parent != NULL) {
       index_t* move = xmalloc(sizeof(index_t));
       *move = current->move_row * width + current->move_col;
       
       enq(moves_reversed, move);
       current = current->parent;
   }
   
   while (!queue_empty(moves_reversed)) {
       index_t* move = (index_t*)deq(moves_reversed);
       enq(S, move);
   }
   
   free_solution(moves_reversed);
   
   return S;
}

solution build_solution(board_t B, board_t target, void* aux) {
   REQUIRES(aux != NULL);
   
   (void)B;
   (void)target;
   (void)aux;
   
   return new_solution();
}

int main(int argc, char** argv) {
   if (argc != 2) {
       fprintf(stderr, "Usage: %s <board-file>\n", argv[0]);
       return 1;
   }
   
   board_t board;
   if (!read_board(argv[1], &board)) {
       fprintf(stderr, "Failed to read board from %s\n", argv[1]);
       return 1;
   }
   
   printf("Solving board...\n");
   solution sol = solve(board);
   
   if (sol == NULL) {
       printf("No solution found!\n");
   } else {
       printf("Solution found!\n");
       free_solution(sol);
   }
   
   free_board(board);
   return 0;
}