/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ft_ten_queens_puzzle.c                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: mel-wahm <mel-wahm@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/21 02:29:22 by q-                #+#    #+#             */
/*   Updated: 2026/07/22 17:12:23 by mel-wahm         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include <unistd.h>
#include <stdlib.h>

static int	absolute(int b)
{
	if (b < 0)
		return (-b);
	else
		return (b);
}

static void	print_position(int *board)
{
	int	i;

	i = 0;
	while (i < 10)
		write(1, &(char){board[i++] + '0'}, 1);
	write(1, "\n", 1);
}

static	int	is_valid(int *board, int col, int row)
{
	int	i;

	i = 0;
	while (i < col)
	{
		if (board[i] == row
			|| (absolute(i - col) == absolute(row - board[i])))
			return (0);
		i++;
	}
	return (1);
}

static void	place(int *board, int col, int *pos)
{
	int	row;
	row = 0;
	if (col == 10)
		return ;
	while (row < 10)
	{
		if (is_valid(board, col, row))
		{
			board[col] = row;
			if (col == 9)
			{
				(*pos)++;
				print_position(board);
				exit(1);
				break ;
			}
			place(board, col + 1, pos);
		}
		row++;
	}
}

int	ft_ten_queens_puzzle(void)
{
	int	pos;
	int	chess_board[10];

	pos = 0;
	place(chess_board, 0, &pos);
	return (pos);
}

int	main()
{
	ft_ten_queens_puzzle();
}
